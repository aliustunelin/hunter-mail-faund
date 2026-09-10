# -*- coding: utf-8 -*-
"""Tavily web arama ile şirket adından resmi site domain'i çözümler."""

from typing import Optional
from urllib.parse import urlparse

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.repositories.api_usage_repo import ApiUsageRepository

logger = get_logger(__name__)

TAVILY_SEARCH_URL = "https://api.tavily.com/search"


def extract_domain(url: str) -> str:
    """URL'den scheme/path temizlenmiş host döner."""
    parsed = urlparse(url)
    host = parsed.netloc or parsed.path
    return host.lower().removeprefix("www.")


class DomainResolver:
    def __init__(self, db: Session):
        self.settings = get_settings()
        self.usage = ApiUsageRepository(db)

    def resolve(self, company_name: str) -> Optional[str]:
        """'official website' sorgusuyla gelen ilk sonucun domain'ini döner."""
        if not self.settings.tavily_enabled:
            logger.warning(
                "TAVILY_API_KEY tanimli degil; domain cozumleme atlandi (%s).",
                company_name,
            )
            return None

        payload = {
            "api_key": self.settings.tavily_api_key,
            "query": f"{company_name} official website Turkey",
            "search_depth": "basic",
            "max_results": 5,
            "include_answer": False,
        }
        try:
            with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
                resp = client.post(TAVILY_SEARCH_URL, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Tavily hatasi (%s): %s", company_name, exc)
            return None
        self.usage.record("tavily", "/search")

        for item in data.get("results", []):
            domain = extract_domain(item.get("url", ""))
            if domain:
                return domain
        return None
