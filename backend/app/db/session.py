"""Database session and engine management."""

import os
from pathlib import Path
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Search for .env in current directory and parent directories
def _load_environment() -> None:
    current = Path(__file__).resolve()
    for parent in [current.parent, current.parents[1], current.parents[2], current.parents[3]]:
        env_file = parent / ".env"
        if env_file.exists():
            load_dotenv(dotenv_path=env_file)
            break


_load_environment()

DATABASE_URL = os.getenv("DATABASE_URL")

_engine = None
_SessionLocal = None


def get_engine():
    """Retrieve or initialize the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            _load_environment()
            db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise RuntimeError("DATABASE_URL is not set in environment or .env file.")
        _engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
    return _engine


def get_session_factory():
    """Retrieve or initialize the session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal


def SessionLocal() -> Session:
    """Convenience callable to instantiate a new Session."""
    factory = get_session_factory()
    return factory()


def get_db() -> Generator[Session, None, None]:
    """FastAPI / context dependency generator for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
