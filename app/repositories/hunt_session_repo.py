# -*- coding: utf-8 -*-
"""Tarama oturumu veri erişim katmanı."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import HuntSession


class HuntSessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, params_json: str) -> HuntSession:
        hunt_session = HuntSession(params_json=params_json)
        self.db.add(hunt_session)
        self.db.flush()
        return hunt_session

    def get(self, session_id: int) -> Optional[HuntSession]:
        return self.db.get(HuntSession, session_id)

    def list(self, limit: int = 20) -> List[HuntSession]:
        return list(
            self.db.scalars(
                select(HuntSession)
                .order_by(HuntSession.id.desc())
                .limit(limit)
            )
        )

    def get_running(self) -> Optional[HuntSession]:
        return self.db.scalars(
            select(HuntSession).where(HuntSession.status == "running")
        ).first()

    def finish(
        self,
        hunt_session: HuntSession,
        status: str,
        error: Optional[str] = None,
    ) -> None:
        hunt_session.status = status
        hunt_session.error = error
        from app.models.entities import utcnow

        hunt_session.finished_at = utcnow()
