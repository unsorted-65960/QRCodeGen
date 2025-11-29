"""
Handles connecting to any external database (MSSQL, MySQL, SQLite, etc.)
and fetching rows dynamically based on the user's saved connection.json.

Also cross-checks each fetched row with the local QR tracking table (qr_records)
to indicate whether a QR code already exists. Includes a cleanup routine
that removes QR records whose image files are missing (or repairs the path
if the file can be found using the hash prefix).
"""

import json
from pathlib import Path
from sqlalchemy import create_engine, text
from database.database import get_session
from database.models import QRRecord
from utils.hash_utils import generate_row_hash
from utils.qr_format_utils import format_row_for_qr


# ------------------- CONFIG LOADER -------------------

def load_connection_config() -> dict:
    """Safely load connection.json from known paths."""
    project_root = Path(__file__).resolve().parents[1]
    possible_paths = [
        project_root / "connection.json",
        project_root / "data" / "connection.json",
        Path.cwd() / "connection.json",
    ]
    for path in possible_paths:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    raise FileNotFoundError("connection.json not found in expected locations.")


# ------------------- DB CONNECTION -------------------

def create_dynamic_engine(cfg: dict):
    """Create SQLAlchemy engine for MSSQL / MySQL / SQLite based on config."""
    db_type = cfg.get("db_type", "").lower()
    host = cfg.get("host", "")
    port = cfg.get("port", "")
    db_name = cfg.get("database", "")
    user = cfg.get("username", "")
    pwd = cfg.get("password", "")
    driver = cfg.get("driver", "")

    if db_type == "sqlite":
        conn_str = f"sqlite:///{db_name}"
    elif db_type == "mssql":
        driver_clause = f"driver={driver or 'ODBC Driver 17 for SQL Server'}"
        conn_str = (
            f"mssql+pyodbc://{user}:{pwd}@{host},{port}/{db_name}"
            f"?trusted_connection=no&{driver_clause.replace(' ', '+')}"
        )
    elif db_type == "mysql":
        conn_str = f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{db_name}"
    else:
        raise ValueError(f"Unsupported db_type: {db_type}")

    return create_engine(conn_str, echo=False, future=True)


# ------------------- ORPHAN CLEANUP -------------------

def cleanup_orphan_qrs(qr_folder: str | Path = "data/output/qrs") -> dict:
    """
    Ensure local QRRecord rows point to existing files. If file missing:
      - Try to find a matching file by hash prefix and repair path,
      - Otherwise delete the QRRecord row.
    """
    qr_dir = Path(qr_folder)
    session = get_session()
    repaired = deleted = 0

    if not qr_dir.exists():
        return {"repaired": 0, "deleted": 0}

    records = session.query(QRRecord).all()
    for rec in records:
        try:
            if rec.qr_path and Path(rec.qr_path).exists():
                continue

            hash_prefix = (rec.hash_code or "")[:12]
            found = None
            if hash_prefix:
                for candidate in qr_dir.glob(f"{hash_prefix}*.png"):
                    if candidate.exists():
                        found = candidate
                        break

            if found:
                rec.qr_path = str(found)
                session.add(rec)
                repaired += 1
            else:
                session.delete(rec)
                deleted += 1
        except Exception:
            try:
                session.delete(rec)
                deleted += 1
            except Exception:
                pass

    session.commit()
    return {"repaired": repaired, "deleted": deleted}


# ------------------- FETCHING LOGIC -------------------

def fetch_products_with_qr_status(limit: int | None = None) -> list[dict]:
    """
    Fetch products (or parts) from the external DB based on selected columns,
    and mark each row with QR generation status.
    Ensures qr_status and qr_hash are included for UI but excluded from QR encoding.
    """
    cfg = load_connection_config()
    table = cfg.get("table")
    columns = cfg.get("columns", [])

    if not table or not columns:
        raise ValueError("connection.json must include 'table' and 'columns'.")

    engine = create_dynamic_engine(cfg)

    col_str = ", ".join(columns)
    query = f"SELECT {col_str} FROM {table}"
    if limit:
        query += f" LIMIT {limit}"

    rows = []
    with engine.connect() as conn:
        result = conn.execute(text(query))
        for row in result.mappings():
            rows.append(dict(row))

    if not rows:
        return []

    cleanup_orphan_qrs()

    session = get_session()
    all_hashes = {r.hash_code for r in session.query(QRRecord.hash_code).all()}

    enriched_rows = []
    for row in rows:
        # Ensure consistent ordering of fields using connection.json order
        ordered_clean_row = {col: row.get(col, "") for col in columns if col in row}

        qr_text = format_row_for_qr(ordered_clean_row)
        qr_hash = generate_row_hash(qr_text)

        row["qr_status"] = "Has QR" if qr_hash in all_hashes else "No QR"
        row["qr_hash"] = qr_hash
        enriched_rows.append(row)

    return enriched_rows


# ------------------- HELPER -------------------

def test_connection_only() -> tuple[bool, str]:
    """Validate current DB credentials from connection.json."""
    try:
        cfg = load_connection_config()
        engine = create_dynamic_engine(cfg)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, f"Successfully connected to {cfg.get('database')} ({cfg.get('db_type')})"
    except Exception as e:
        return False, str(e)
