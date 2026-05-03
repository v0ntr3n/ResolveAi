from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Base model for SQLAlchemy tables."""


def get_engine(database_url: str | None = None) -> Engine:
    settings = get_settings()
    resolved_url = database_url or settings.DATABASE_URL
    if resolved_url.startswith("sqlite:///./"):
        Path("data").mkdir(exist_ok=True)
    return create_engine(resolved_url, connect_args={"check_same_thread": False} if "sqlite" in resolved_url else {})


def get_session_factory(database_url: str | None = None) -> sessionmaker:
    return sessionmaker(bind=get_engine(database_url), expire_on_commit=False)
