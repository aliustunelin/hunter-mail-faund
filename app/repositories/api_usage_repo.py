# -*- coding: utf-8 -*-
"""Harici API kullanım (kredi) takibi — veri erişim katmanı."""

from typing import Dict, List

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import ApiUsage


class ApiUsageRepository:
    def __init__(self, db: Session):
        self.db = db

    def record(
        self, provider: str, endpoint: str, credits_spent: int = 0
    ) -> None:
        self.db.add(
            ApiUsage(
                provider=provider,
                endpoint=endpoint,
                credits_spent=credits_spent,
            )
        )

    def summary(self) -> List[Dict[str, int]]:
        rows = self.db.execute(
            select(
                ApiUsage.provider,
                func.count(ApiUsage.id),
                func.sum(ApiUsage.credits_spent),
            ).group_by(ApiUsage.provider)
        ).all()
        return [
            {
                "provider": provider,
                "calls": int(calls or 0),
                "credits_spent": int(credits or 0),
            }
            for provider, calls, credits in rows
        ]
