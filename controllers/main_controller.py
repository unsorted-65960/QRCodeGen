from PySide6.QtWidgets import QInputDialog, QMessageBox, QLineEdit, QApplication
from database.database import get_session
from views.main_view import MainView
from controllers.connection_manager_controller import ConnectionManagerController
from controllers.qr_preview_controller import QRPreviewController
from database import fetcher


class MainController:
    """Main controller managing app flow, DB fetching, and QR workflows."""

    def __init__(self):
        self.view = MainView()
        self.session = get_session()
        self.conn_controller = None
        self.qr_preview_controller = None
        self._is_loading = False
        self.connect_signals()

    # ------------------------------------------------------------------
    # SIGNALS
    # ------------------------------------------------------------------
    def connect_signals(self):
        self.view.refresh_requested.connect(self.load_products)
        self.view.print_requested.connect(self.handle_print)
        self.view.connect_db_clicked.connect(self.open_connection_manager)
        self.view.generate_qr_clicked.connect(self.handle_generate_qr)

    # ------------------------------------------------------------------
    # SHOW MAIN WINDOW
    # ------------------------------------------------------------------
    def show_main_window(self):
        self.load_products()
        self.view.show()

    # ------------------------------------------------------------------
    # LOAD PRODUCTS FROM EXTERNAL DATABASE
    # ------------------------------------------------------------------
    def load_products(self):
        """Load products from the external database and update the table."""
        if self._is_loading:
            return

        self._is_loading = True
        try:
            fetcher.test_connection_only()
            products = fetcher.fetch_products_with_qr_status()
            self.view.populate_table(products)
            QApplication.processEvents()
        except FileNotFoundError:
            QMessageBox.warning(
                self.view,
                "No DB Config",
                "connection.json not found. Please configure DB connection via Connect DB."
            )
            self.view.populate_table([])
        except Exception as e:
            QMessageBox.warning(
                self.view,
                "Failed to Load Products",
                f"Error: {e}"
            )
            self.view.populate_table([])
        finally:
            self._is_loading = False

    # ------------------------------------------------------------------
    # GENERATE QR (Preview Workflow)
    # ------------------------------------------------------------------
    def handle_generate_qr(self, row_data: dict):
        """Open QR preview window and handle save callback."""
        try:
            from database.fetcher import load_connection_config
            cfg = load_connection_config()
            valid_columns = set(cfg.get("columns", []))

            # Filter only valid columns for QR generation
            clean_row = {k: v for k, v in row_data.items() if k in valid_columns}
            if not clean_row:
                QMessageBox.warning(
                    self.view,
                    "Invalid Data",
                    "No valid columns found to encode from this row.\n"
                    "Please check your column selections in Connection Manager."
                )
                return

            # Create preview controller with callback
            self.qr_preview_controller = QRPreviewController(clean_row, on_saved=self._on_qr_saved)
            self.qr_preview_controller.show()

        except Exception as e:
            QMessageBox.warning(
                self.view,
                "QR Preview Error",
                f"Error preparing QR preview:\n{e}"
            )

    # ------------------------------------------------------------------
    # QR SAVED CALLBACK
    # ------------------------------------------------------------------
    def _on_qr_saved(self):
        """Triggered after successful QR save to refresh the table."""
        try:
            self.load_products()
        except Exception as e:
            QMessageBox.warning(
                self.view,
                "Refresh Failed",
                f"Could not refresh after saving QR:\n{e}"
            )

    # ------------------------------------------------------------------
    # PRINT LABELS
    # ------------------------------------------------------------------
    def handle_print(self, selected_products, qty):
        """Generate printable labels for selected products with dynamic QR lookup."""
        from utils.pdf_utils import generate_label_pdf
        from pathlib import Path

        if not selected_products or not isinstance(selected_products, list):
            QMessageBox.warning(
                self.view,
                "Invalid Selection",
                "No valid products selected for printing."
            )
            return

        if not isinstance(qty, dict) or not qty:
            QMessageBox.warning(
                self.view,
                "Invalid Quantity Data",
                "Invalid or missing quantity data."
            )
            return

        try:
            pdf_path, skipped = generate_label_pdf(selected_products, qty)

            if not pdf_path:
                QMessageBox.warning(
                    self.view,
                    "No Labels Generated",
                    "No labels could be generated because no QR codes were found."
                )
                return

            # Success message
            msg = f"✅ Labels saved successfully to:\n{Path(pdf_path).resolve()}"
            if skipped:
                msg += f"\n\n⚠️ Skipped {len(skipped)} item(s) with missing QR data."

            QMessageBox.information(
                self.view,
                "Label Generation Complete",
                msg
            )

            # Optional: refresh main table after printing
            try:
                self.load_products()
            except Exception:
                pass

        except Exception as e:
            QMessageBox.warning(
                self.view,
                "Label Generation Failed",
                f"Error while creating labels:\n{e}"
            )

    # ------------------------------------------------------------------
    # CONNECTION MANAGER
    # ------------------------------------------------------------------
    def open_connection_manager(self):
        """Require admin password before opening the connection manager."""
        password, ok = QInputDialog.getText(
            self.view,
            "Admin Access Required",
            "Enter admin password:",
            echo=QLineEdit.EchoMode.Password,
        )

        if not ok:
            return

        if password.strip() != "admin123":
            QMessageBox.warning(
                self.view,
                "Access Denied",
                "Incorrect password."
            )
            return

        self.conn_controller = ConnectionManagerController(on_saved=self.load_products)
        self.conn_controller.show()
