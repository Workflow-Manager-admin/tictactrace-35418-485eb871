from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base
import os

# PUBLIC_INTERFACE
def get_database_url() -> str:
    """
    Returns the database URL. Uses SQLITE_URL env var, else defaults to SQLite in project dir.
    """
    db_url = os.getenv("SQLITE_URL")
    if db_url:
        return db_url
    return "sqlite:///./tic_tac_toe.db"

SQLALCHEMY_DATABASE_URL = get_database_url()
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# PUBLIC_INTERFACE
def init_db():
    """Create all tables if not present."""
    Base.metadata.create_all(bind=engine)
