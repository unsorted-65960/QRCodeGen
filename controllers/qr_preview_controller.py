from PySide6.QtWidgets import QMessageBox, QApplication
from datetime import datetime
from pathlib import Path

from views.qr_preview_view import QRPreviewView
from database.database import get_session
from database.models import QRRecord
from utils.qr_utils import generate_qr_image, save_qr_image
from utils.qr_format_utils import format_row_for_qr, make_preview_text
from utils.hash_utils import generate_row_hash
from database.fetcher import load_connection_config


class QRPreviewController:
    """Handles the QR preview workflow before saving."""

    def __init__(self, row_data: dict, on_saved=None):
        self.view = None
        self.session = get_session()
        self.row_data = row_data
        self.on_saved = on_saved
        self._last_qr_image = None
        self._last_qr_text = None
        self._clean_row = None
        self._saved = False  # guard to prevent double saves
        self._build_preview()

    # ------------------------------------------------------------------
    def _build_preview(self):
        """Prepare the QR text and preview for the given row."""
        try:
            cfg = load_connection_config()
            cfg_cols = cfg.get("columns", [])
            valid_columns = set(cfg_cols)

            # Keep only user-selected columns in configured order
            self._clean_row = {col: self.row_data.get(col, "") for col in cfg_cols if col in self.row_data}
            if not self._clean_row:
                raise ValueError("No valid columns to encode. Check connection.json column mapping.")

            # Generate QR text & image
            self._last_qr_text = format_row_for_qr(self._clean_row)
            self._last_qr_image = generate_qr_image(self._last_qr_text)

            # Initialize the preview UI
            self.view = QRPreviewView(
                qr_text=self._last_qr_text,
                qr_image=self._last_qr_image,
                row_data=self._clean_row,
            )

            self.view.display_qr_image(self._last_qr_image)
            self._connect_signals()

        except Exception as e:
            QMessageBox.warning(None, "QR Preview Error", f"Error building preview:\n{e}")

    # ------------------------------------------------------------------
    def _connect_signals(self):
        self.view.confirm_clicked.connect(self._handle_confirm_save)
        self.view.cancel_clicked.connect(self._handle_cancel)

    # ------------------------------------------------------------------
    def show(self):
        """Display the preview window."""
        if self.view:
            self.view.show()

    # ------------------------------------------------------------------
    def _handle_confirm_save(self):
        """Save the generated QR image and DB record."""
        try:
            if self._saved:
                return

            if not self._last_qr_image or not self._clean_row:
                QMessageBox.warning(self.view, "Missing Data", "QR image or data is missing.")
                return

            qr_text = self._last_qr_text
            qr_hash = generate_row_hash(qr_text)

            # Prevent duplicates
            if self.session.query(QRRecord).filter_by(hash_code=qr_hash).first():
                QMessageBox.information(self.view, "Already Exists", "This record already has a saved QR.")
                self.view.close()
                QApplication.processEvents()
                return

            # Prepare output directory
            qr_dir = Path("data/output/qrs")
            qr_dir.mkdir(parents=True, exist_ok=True)

            # Save QR image
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{qr_hash[:12]}_{ts}.png"
            save_path = qr_dir / filename
            save_qr_image(self._last_qr_image, str(save_path))

            # Record into app.db
            preview = make_preview_text(self._clean_row)
            record = QRRecord(
                hash_code=qr_hash,
                qr_path=str(save_path),
                preview_text=preview,
            )
            self.session.add(record)
            self.session.commit()
            self.session.flush()
            self.session.expire_all()

            QMessageBox.information(self.view, "QR Saved", f"QR Code saved to:\n{save_path}")

            # Close preview safely
            self._saved = True
            self.view.close()
            QApplication.processEvents()

            # Notify main controller to refresh
            if callable(self.on_saved):
                self.on_saved()

        except Exception as e:
            QMessageBox.warning(self.view, "QR Save Error", f"Error saving QR:\n{e}")

    # ------------------------------------------------------------------
    def _handle_cancel(self):
        """Close preview without saving anything."""
        self.view.close()
        QApplication.processEvents()
