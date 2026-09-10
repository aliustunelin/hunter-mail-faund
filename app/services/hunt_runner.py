# -*- coding: utf-8 -*-
"""Arka plan tarama görevi — FastAPI BackgroundTasks tarafından çağrılır.

Kendi DB oturumunu açar; API isteğinin oturumu yanıtla birlikte kapansa da
tarama devam eder.
"""

from app.core.logging import get_logger
from app.db.database import SessionLocal
from app.repositories.hunt_session_repo import HuntSessionRepository
from app.services.hunt_service import HuntService

logger = get_logger(__name__)


def run_hunt_in_background(session_id: int, params: dict) -> None:
    db = SessionLocal()
    try:
        session_repo = HuntSessionRepository(db)
        hunt_session = session_repo.get(session_id)
        if hunt_session is None:
            logger.error("Tarama oturumu bulunamadi: #%s", session_id)
            return

        service = HuntService(db)
        try:
            service.execute(hunt_session, **params)
            db.commit()
            session_repo.finish(hunt_session, "completed")
        except Exception as exc:
            db.rollback()
            logger.exception("Tarama basarisiz (oturum #%s)", session_id)
            hunt_session = session_repo.get(session_id)
            if hunt_session is not None:
                session_repo.finish(hunt_session, "failed", str(exc)[:2000])
        db.commit()
    finally:
        db.close()
