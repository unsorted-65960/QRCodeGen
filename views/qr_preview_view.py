from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QScrollArea, QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage
from io import BytesIO


class QRPreviewView(QWidget):
    """Displays a preview of the QR code and encoded data before saving."""

    confirm_clicked = Signal()
    cancel_clicked = Signal()

    def __init__(self, qr_text: str = "", qr_image=None, row_data: dict = None):
        super().__init__()
        self.setWindowTitle("QR Code Preview")
        self.resize(700, 550)
        self.qr_text = qr_text
        self.row_data = row_data or {}
        self.qr_image = qr_image

        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # ---------------- Header ----------------
        title_label = QLabel("Preview QR Code & Details")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 16pt;
            font-weight: bold;
            color: #222;
        """)
        layout.addWidget(title_label)

        # ---------------- Content Area ----------------
        content_layout = QHBoxLayout()
        layout.addLayout(content_layout, 3)

        # --- Left side: QR Image ---
        qr_container = QVBoxLayout()
        qr_label = QLabel()
        qr_label.setFixedSize(250, 250)
        qr_label.setAlignment(Qt.AlignCenter)
        qr_label.setStyleSheet("""
            QLabel {
                border: 1px solid #d0d4da;
                background-color: white;
                border-radius: 12px;
            }
        """)
        self.qr_label = qr_label
        qr_container.addWidget(qr_label, alignment=Qt.AlignCenter)

        qr_container.addItem(QSpacerItem(0, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        content_layout.addLayout(qr_container, 1)

        # --- Right side: Encoded fields ---
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Encoded Data (from selected database row):"))

        # Scrollable field list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        frame = QFrame()
        frame_layout = QVBoxLayout(frame)

        for key, value in self.row_data.items():
            lbl = QLabel(f"<b>{key.replace('_', ' ').title()}:</b> {value}")
            lbl.setWordWrap(True)
            frame_layout.addWidget(lbl)

        frame_layout.addStretch()
        scroll.setWidget(frame)
        right_layout.addWidget(scroll, 3)

        # Raw text box (multi-line, read-only)
        right_layout.addWidget(QLabel("Encoded QR Text:"))
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setText(self.qr_text)
        right_layout.addWidget(self.text_area, 2)

        content_layout.addLayout(right_layout, 2)

        # ---------------- Footer Buttons ----------------
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.confirm_btn = QPushButton("✅ Confirm & Save")
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #1084e0; }
            QPushButton:pressed { background-color: #006bb3; }
        """)

        self.cancel_btn = QPushButton("❌ Cancel")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f1f1;
                color: #333;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #e0e0e0; }
            QPushButton:pressed { background-color: #d0d0d0; }
        """)

        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.confirm_btn)

        layout.addLayout(button_layout)

        # ---------------- Connections ----------------
        self.confirm_btn.clicked.connect(self.confirm_clicked.emit)
        self.cancel_btn.clicked.connect(self.cancel_clicked.emit)

    # ------------------------------------------------------------------
    def display_qr_image(self, pil_image):
        """Display PIL QR image inside QLabel."""
        if not pil_image:
            return

        # Convert PIL image to QPixmap
        buf = BytesIO()
        pil_image.save(buf, format="PNG")
        qimg = QImage.fromData(buf.getvalue())
        pix = QPixmap.fromImage(qimg)

        scaled_pix = pix.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.qr_label.setPixmap(scaled_pix)

    # ------------------------------------------------------------------
    def set_qr_text(self, text: str):
        """Update the raw encoded text preview."""
        self.qr_text = text
        self.text_area.setText(text)
