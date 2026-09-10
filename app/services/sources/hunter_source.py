# -*- coding: utf-8 -*-
"""Hunter.io domain-search kaynağı + kredi/hesap takibi."""

from typing import List, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.repositories.api_usage_repo import ApiUsageRepository
from app.services.findings import SOURCE_CONFIDENCE, EmailFinding, classify_email_type

logger = get_logger(__name__)

API_BASE = "https://api.hunter.io/v2"


class HunterSource:
    """Kredi harcayan tek kaynak; kullanım api_usage tablosuna yazılır."""

    SOURCE_NAME = "hunter"

    def __init__(self, db: Session):
        self.settings = get_settings()
        self.usage = ApiUsageRepository(db)

    def credits_left(self) -> Optional[int]:
        """Hunter hesabındaki kalan arama kredisi; hata olursa None."""
        if not self.settings.hunter_enabled:
            return 0
        try:
            with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
                resp = client.get(
                    f"{API_BASE}/account",
                    params={"api_key": self.settings.hunter_api_key},
                )
                resp.raise_for_status()
                data = resp.json().get("data", {})
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Hunter account sorgusu basarisiz: %s", exc)
            return None
        self.usage.record("hunter", "/account")
        calls = data.get("calls", {}) or {}
        left = calls.get("available")
        if left is None:
            left = data.get("searches_left")
        return left if isinstance(left, int) else None

    def search(self, domain: str) -> List[EmailFinding]:
        if not self.settings.hunter_enabled:
            logger.info(
                "HUNTER_API_KEY tanimli degil; hunter kaynagi atlandi (%s).", domain
            )
            return []

        try:
            with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
                resp = client.get(
                    f"{API_BASE}/domain-search",
                    params={
                        "domain": domain,
                        "api_key": self.settings.hunter_api_key,
                        "limit": self.settings.hunter_domain_limit,
                    },
                )
                resp.raise_for_status()
                payload = resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Hunter hatasi (%s): %s", domain, exc)
            return []

        emails = payload.get("data", {}).get("emails", []) or []
        self.usage.record("hunter", "/domain-search", credits_spent=len(emails))

        findings: List[EmailFinding] = []
        for item in emails:
            address = item.get("value")
            if not address:
                continue
            findings.append(
                EmailFinding(
                    address=address,
                    source=self.SOURCE_NAME,
                    confidence=float(
                        item.get("confidence") or SOURCE_CONFIDENCE[self.SOURCE_NAME]
                    ),
                    first_name=item.get("first_name"),
                    last_name=item.get("last_name"),
                    position=item.get("position"),
                    type=item.get("type") or classify_email_type(address),
                )
            )
        return findings
