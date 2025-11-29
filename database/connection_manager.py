# database/connection_manager.py
import sqlalchemy
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError
from utils.config_manager import get_active_config

def build_connection_url(config):
    db_type = config.get("db_type", "").lower()
    
    if db_type == "mssql":
        driver = config.get("driver", "ODBC Driver 17 for SQL Server")
        return (
            f"mssql+pyodbc://{config['username']}:{config['password']}@"
            f"{config['host']},{config.get('port', 1433)}/{config['database']}"
            f"?driver={driver.replace(' ', '+')}"
        )
    
    elif db_type == "mysql":
        return (
            f"mysql+pymysql://{config['username']}:{config['password']}@"
            f"{config['host']}:{config.get('port', 3306)}/{config['database']}"
        )

    elif db_type == "sqlite":
        return f"sqlite:///{config['database']}"

    else:
        raise ValueError(f"Unsupported database type: {db_type}")

def test_connection(config=None):
    config = config or get_active_config()
    if not config:
        return False, "No connection configuration found."

    try:
        url = build_connection_url(config)
        engine = create_engine(url, echo=False, future=True)
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
        return True, "Connection successful."
    except SQLAlchemyError as e:
        return False, f"Connection failed: {e}"

def get_engine():
    """Return SQLAlchemy engine using saved config."""
    config = get_active_config()
    if not config:
        return None
    try:
        url = build_connection_url(config)
        return create_engine(url, echo=False, future=True)
    except Exception as e:
        print(f"⚠️ Failed to create engine: {e}")
        return None
