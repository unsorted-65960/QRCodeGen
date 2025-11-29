# database/models.py
from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from datetime import datetime
from .database import Base


class QRRecord(Base):
    """
    Tracks generated QR codes corresponding to rows from an external database.

    Each record represents one unique QR identity, determined by hashing
    the concatenated text of the selected columns for that row.
    """

    __tablename__ = "qr_records"
    __table_args__ = (UniqueConstraint("hash_code", name="uq_qr_hash"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    hash_code = Column(String, nullable=False, unique=True)  # 🔹 Deterministic hash of row text
    qr_path = Column(String, nullable=False)                 # 🔹 Local path to QR PNG
    preview_text = Column(String, nullable=True)             # 🔹 Human-readable summary of QR content
    created_at = Column(DateTime, default=datetime.now)      # 🔹 Timestamp of creation

    def as_dict(self):
        """Return a dictionary representation of this record."""
        return {
            "id": self.id,
            "hash_code": self.hash_code,
            "qr_path": self.qr_path,
            "preview_text": self.preview_text,
            "created_at": (
                self.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if self.created_at else None
            ),
        }
