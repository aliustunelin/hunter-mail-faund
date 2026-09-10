# -*- coding: utf-8 -*-
"""Tarama (hunt) endpoint şemaları."""

import json
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

DEFAULT_SOURCES = ["crtsh", "contact_page", "tavily"]


class HuntRunRequest(BaseModel):
    categories: Optional[List[str]] = None
    companies: Optional[List[str]] = None
    sources: List[str] = Field(default_factory=lambda: list(DEFAULT_SOURCES))
    use_hunter: bool = False
    resolve_missing_domains: bool = True
    verify_emails: bool = True


class HuntSessionOut(BaseModel):
    id: int
    status: str
    params: Optional[dict] = None
    companies_scanned: int
    emails_found: int
    new_emails: int
    error: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None

    @classmethod
    def from_entity(cls, hunt_session) -> "HuntSessionOut":
        params = None
        if hunt_session.params_json:
            try:
                params = json.loads(hunt_session.params_json)
            except ValueError:
                params = None
        return cls(
            id=hunt_session.id,
            status=hunt_session.status,
            params=params,
            companies_scanned=hunt_session.companies_scanned,
            emails_found=hunt_session.emails_found,
            new_emails=hunt_session.new_emails,
            error=hunt_session.error,
            started_at=hunt_session.started_at,
            finished_at=hunt_session.finished_at,
        )


class HunterCreditsOut(BaseModel):
    enabled: bool
    credits_left: Optional[int] = None
