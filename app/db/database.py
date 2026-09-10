# -*- coding: utf-8 -*-
"""SQLite engine, session fabrikası ve şema kurulumu."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # FastAPI threadpool + arka plan görevi
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _connection_record):
    # Arka plan taraması yazarken API okumaları bloklanmasın
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.db import seed
    from app.models import entities  # noqa: F401 — modelleri Base'e kaydet

    Base.metadata.create_all(bind=engine)
    seed.run(SessionLocal)
