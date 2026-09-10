# -*- coding: utf-8 -*-
"""Şirket sitesinin iletişim/iletişim-benzeri sayfalarından email toplar.

mailto: linkleri ve sayfa metninde geçen @domain adresleri ayıklanır.
Yönlendirme sonunda farklı bir domaine (ör. obss.com.tr -> obss.tech)
düşülürse o host'taki adresler de kabul edilir.
"""

import re
import time
from typing import List, Optional, Set, Tuple

import httpx
from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.findings import SOURCE_CONFIDENCE, EmailFinding, classify_email_type

logger = get_logger(__name__)

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
# logo@2x.png gibi yanlış eşleşmeleri elemek için
JUNK_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".css", ".js")
USER_AGENT = {"User-Agent": "Mozilla/5.0 (compatible; HunterMailFound/1.0)"}


class ContactPageScraper:
    SOURCE_NAME = "contact_page"
    CANDIDATE_PATHS = (
        "",
        "iletisim",
        "contact",
        "contact-us",
        "iletisim.html",
        "hakkimizda",
        "about",
        "destek",
        "support",
    )

    def search(self, domain: str) -> List[EmailFinding]:
        settings = get_settings()
        hosts: Set[str] = {domain}
        pages: List[str] = []
        with httpx.Client(
            timeout=settings.request_timeout_seconds,
            headers=USER_AGENT,
            follow_redirects=True,
        ) as client:
            for path in self.CANDIDATE_PATHS:
                kind, html, final_host = self._fetch(client, f"https://{domain}/{path}")
                if kind == "unreachable" and path and not path.endswith(".html"):
                    kind, html, final_host = self._fetch(
                        client, f"http://{domain}/{path}"
                    )
                if kind == "ok":
                    if final_host:
                        hosts.add(final_host.removeprefix("www."))
                    pages.append(html)
                time.sleep(settings.inter_source_delay_seconds)

        found = set()
        for html in pages:
            found.update(self._extract_emails(html, hosts))

        return [
            EmailFinding(
                address=email,
                source=self.SOURCE_NAME,
                confidence=SOURCE_CONFIDENCE[self.SOURCE_NAME],
                type=classify_email_type(email),
            )
            for email in sorted(found)
        ]

    def _fetch(
        self, client: httpx.Client, url: str
    ) -> Tuple[str, Optional[str], Optional[str]]:
        """('ok'|'empty'|'unreachable', html, final_host) döner.

        'unreachable' yalnızca bağlantı kurulamadığında döner; HTTP 4xx/5xx
        geldiğinde http:// tekrarı anlamsızdır ('empty').
        """
        try:
            resp = client.get(url)
        except httpx.HTTPError:
            return "unreachable", None, None
        if resp.status_code != 200:
            return "empty", None, None
        if "text/html" not in resp.headers.get("content-type", ""):
            return "empty", None, None
        return "ok", resp.text, resp.url.host

    def _extract_emails(self, html: str, hosts: Set[str]) -> List[str]:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()

        candidates = set()
        for a in soup.select("a[href^='mailto:']"):
            address = (
                a.get("href", "")[len("mailto:"):].split("?", 1)[0].strip().lower()
            )
            if EMAIL_RE.fullmatch(address):
                candidates.add(address)
        for match in EMAIL_RE.findall(soup.get_text(" ")):
            candidates.add(match.lower().strip("."))

        result = []
        for address in sorted(candidates):
            local, _, host = address.partition("@")
            if not self._host_accepted(host, hosts):
                continue
            if address.endswith(JUNK_SUFFIXES) or local.endswith(JUNK_SUFFIXES):
                continue
            if len(address) > 254:
                continue
            result.append(address)
        return result

    @staticmethod
    def _host_accepted(host: str, hosts: Set[str]) -> bool:
        return any(
            host == h or host.endswith("." + h) for h in hosts
        )
