# -*- coding: utf-8 -*-
"""Tavily arama sonuçlarından email ayıklayan kaynak.

'"@domain" email iletisim contact' tarzı sorguyla gelen sayfa içeriklerinde
hedef domain'e ait adresler aranır. Kullanım api_usage tablosuna yazılır.
"""

import re
from typing import List

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.repositories.api_usage_repo import ApiUsageRepository
from app.services.findings import SOURCE_CONFIDENCE, EmailFinding, classify_email_type

logger = get_logger(__name__)

TAVILY_SEARCH_URL = "https://api.tavily.com/search"
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")


class TavilyDorkSource:
    SOURCE_NAME = "tavily"

    def __init__(self, db: Session):
        self.settings = get_settings()
        self.usage = ApiUsageRepository(db)

    def search(self, domain: str) -> List[EmailFinding]:
        if not self.settings.tavily_enabled:
            logger.info(
                "TAVILY_API_KEY tanimli degil; tavily kaynagi atlandi (%s).", domain
            )
            return []

        payload = {
            "api_key": self.settings.tavily_api_key,
            "query": f'"@{domain}" email iletisim contact',
            "search_depth": "basic",
            "max_results": 10,
            "include_answer": False,
        }
        try:
            with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
                resp = client.post(TAVILY_SEARCH_URL, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Tavily hatasi (%s): %s", domain, exc)
            return []
        self.usage.record("tavily", "/search")

        emails = set()
        for item in data.get("results", []):
            blob = " ".join(
                (
                    item.get("url", ""),
                    item.get("title", ""),
                    item.get("content", ""),
                )
            )
            for match in EMAIL_RE.findall(blob):
                match = match.lower().strip(".")
                host = match.partition("@")[2]
                if host == domain or host.endswith("." + domain):
                    emails.add(match)

        return [
            EmailFinding(
                address=email,
                source=self.SOURCE_NAME,
                confidence=SOURCE_CONFIDENCE[self.SOURCE_NAME],
                type=classify_email_type(email),
            )
            for email in sorted(emails)
        ]
