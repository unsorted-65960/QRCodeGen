# database/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

DB_PATH = Path("data") / "app.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# sqlite file (local)
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_session():
    return SessionLocal()

def init_db(Base):
    Base.metadata.create_all(bind=engine)
