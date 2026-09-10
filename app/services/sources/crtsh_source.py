# -*- coding: utf-8 -*-
"""crt.sh Certificate Transparency kaynağı.

Sertifika şeffaflık kayıtlarındaki (common_name / name_value) alanlardan
hedef domain'e ait email adreslerini ayıklar. Ücretsiz, anahtar gerektirmez.
"""

import re
import time
from typing import List

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.findings import SOURCE_CONFIDENCE, EmailFinding, classify_email_type

logger = get_logger(__name__)

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

# crt.sh ara sıra 502/503 döner; kısa beklemeyle tekrar denenir
MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 3.0
RETRYABLE_STATUS = {502, 503, 504}


class CrtShSource:
    SOURCE_NAME = "crtsh"
    URL = "https://crt.sh/"

    def search(self, domain: str) -> List[EmailFinding]:
        settings = get_settings()
        rows = self._fetch_rows(domain, settings.crtsh_timeout_seconds)
        if rows is None:
            return []

        emails = set()
        for row in rows:
            blob = " ".join(
                str(row.get(key) or "")
                for key in ("common_name", "name_value", "issuer_name")
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

    def _fetch_rows(self, domain: str, timeout: float):
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            for attempt in range(1, MAX_ATTEMPTS + 1):
                try:
                    resp = client.get(
                        self.URL, params={"q": f"%.{domain}", "output": "json"}
                    )
                    if resp.status_code in RETRYABLE_STATUS and attempt < MAX_ATTEMPTS:
                        logger.info(
                            "crt.sh %s (%s), deneme %d/%d...",
                            resp.status_code,
                            domain,
                            attempt,
                            MAX_ATTEMPTS,
                        )
                        time.sleep(RETRY_DELAY_SECONDS)
                        continue
                    resp.raise_for_status()
                    return resp.json()
                except (httpx.HTTPError, ValueError) as exc:
                    if attempt < MAX_ATTEMPTS:
                        time.sleep(RETRY_DELAY_SECONDS)
                        continue
                    logger.warning("crt.sh hatasi (%s): %s", domain, exc)
                    return None
