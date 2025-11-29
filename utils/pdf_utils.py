# utils/pdf_utils.py
from pathlib import Path
from datetime import datetime
import os

# Setup environment (WeasyPrint DLLs)
from utils.env_loader import setup_local_dlls
setup_local_dlls()

from weasyprint import HTML

# DB + models
from database.database import get_session
from database.models import QRRecord
from utils.config_manager import get_active_config

# Hash helper
from utils.hash_utils import generate_row_hash

# Template renderer
from utils.label_template import render_label_html, CSS


def _safe_join_columns(product: dict, columns: list[str]) -> str:
    """Join column values in given order (use empty string for missing)."""
    return "|".join(str(product.get(col, "")) for col in columns)


def generate_label_pdf(selected_products: list[dict], quantity_map: dict):
    """
    Generate printable PDF labels dynamically based on selected columns.
    Returns: (pdf_path, skipped_list)
    """
    base_output = Path("data/output")
    qr_dir = base_output / "qrs"
    label_dir = base_output / "labels"
    qr_dir.mkdir(parents=True, exist_ok=True)
    label_dir.mkdir(parents=True, exist_ok=True)

    # Load column order from connection.json
    config = get_active_config() or {}
    columns_order = config.get("columns", [])

    session = get_session()

    html_parts = ["<html><head>", CSS, "</head><body>"]

    skipped = []
    any_label_added = False

    for product in selected_products:

        # Lookup row index
        row_index = product.get("_row")
        qty = quantity_map.get(row_index, 1)

        # Resolve hash
        qr_hash = product.get("qr_hash") or product.get("hash_code")
        if not qr_hash:
            qr_hash = generate_row_hash(_safe_join_columns(product, columns_order))

        qr_record = session.query(QRRecord).filter_by(hash_code=str(qr_hash)).first()

        if not qr_record:
            skipped.append((product, "qr_not_found_in_local_db"))
            continue

        qr_path = Path(qr_record.qr_path)
        if not qr_path.exists():
            skipped.append((product, "qr_file_missing"))
            continue

        qr_src = qr_path.as_posix()
        any_label_added = True

        # Create HTML copies based on quantity
        for _ in range(qty):
            html_parts.append(
                render_label_html(qr_src, product, columns_order)
            )

    html_parts.append("</body></html>")
    full_html = "".join(html_parts)

    if not any_label_added:
        return None, skipped

    pdf_name = f"Labels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = label_dir / pdf_name

    HTML(string=full_html, base_url=os.getcwd()).write_pdf(str(pdf_path))

    try:
        os.startfile(pdf_path)
    except Exception:
        pass

    return pdf_path, skipped
