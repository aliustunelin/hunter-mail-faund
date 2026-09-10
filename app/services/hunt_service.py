# -*- coding: utf-8 -*-
"""Tarama orkestrasyonu (iş katmanının çekirdeği).

Akış: domain çöz → seçili kaynakları çalıştır → bulguları birleştir →
yeni adresleri doğrula → veritabanına yaz → oturum sayaçlarını güncelle.
"""

import time
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.entities import Company, HuntSession
from app.repositories.company_repo import CompanyRepository
from app.repositories.email_repo import EmailRepository
from app.services import findings as finding_rules
from app.services.domain_resolver import DomainResolver
from app.services.email_verifier import EmailVerifier
from app.services.findings import EmailFinding
from app.services.sources.contact_scraper import ContactPageScraper
from app.services.sources.crtsh_source import CrtShSource
from app.services.sources.hunter_source import HunterSource
from app.services.sources.tavily_dork_source import TavilyDorkSource

logger = get_logger(__name__)

DEFAULT_SOURCES = ["crtsh", "contact_page", "tavily"]
ALL_SOURCES = ["hunter", "crtsh", "contact_page", "tavily"]

TYPE_WEIGHT = {"personal": 3, "generic": 2, "unknown": 1, "system": 0}


class HuntService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.company_repo = CompanyRepository(db)
        self.email_repo = EmailRepository(db)
        self.domain_resolver = DomainResolver(db)
        self.verifier = EmailVerifier()
        self.sources = {
            "hunter": HunterSource(db),
            "crtsh": CrtShSource(),
            "contact_page": ContactPageScraper(),
            "tavily": TavilyDorkSource(db),
        }

    def execute(
        self,
        hunt_session: HuntSession,
        categories: Optional[List[str]] = None,
        company_names: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        resolve_missing_domains: bool = True,
        verify_emails: bool = True,
    ) -> None:
        selected = [s for s in (sources or DEFAULT_SOURCES) if s in self.sources]
        companies = self.company_repo.list_for_hunt(
            categories=categories, names=company_names
        )
        logger.info(
            "Tarama basliyor: %d sirket, kaynaklar=%s (oturum #%s)",
            len(companies),
            ",".join(selected),
            hunt_session.id,
        )
        if not companies:
            logger.warning("Tarama kapsaminda sirket bulunamadi.")

        for company in companies:
            try:
                found, new = self._process_company(
                    company, selected, resolve_missing_domains, verify_emails
                )
                hunt_session.companies_scanned += 1
                hunt_session.emails_found += found
                hunt_session.new_emails += new
            except Exception as exc:  # tek şirket tüm taramayı düşürmesin
                logger.exception("Sirket islenemedi (%s): %s", company.name, exc)
            self.db.commit()
            time.sleep(self.settings.inter_company_delay_seconds)

        logger.info(
            "Tarama bitti (oturum #%s): %d sirket, %d adres (%d yeni).",
            hunt_session.id,
            hunt_session.companies_scanned,
            hunt_session.emails_found,
            hunt_session.new_emails,
        )

    def _process_company(
        self,
        company: Company,
        sources: List[str],
        resolve_domains: bool,
        verify: bool,
    ) -> Tuple[int, int]:
        domain = company.domain
        if not domain and resolve_domains:
            domain = self.domain_resolver.resolve(company.name)
            if domain:
                self.company_repo.set_domain(company, domain, "tavily")
        if not domain:
            logger.info("Domain bulunamadi, atlandi: %s", company.name)
            return 0, 0

        logger.info("[%s] %s taraniyor (kaynaklar: %s)", company.name, domain, ",".join(sources))

        by_address: Dict[str, List[EmailFinding]] = {}
        for name in sources:
            try:
                results = self.sources[name].search(domain)
            except Exception as exc:
                logger.warning("Kaynak hatasi %s (%s): %s", name, domain, exc)
                continue
            for finding in results:
                by_address.setdefault(finding.address.lower(), []).append(finding)
            time.sleep(self.settings.inter_source_delay_seconds)

        new_count = 0
        for address, group in by_address.items():
            merged = self._merge(address, group)
            email, is_new = self.email_repo.upsert_finding(company, merged)
            if is_new:
                new_count += 1
                if verify:
                    status, normalized = self.verifier.verify(address)
                    email.verification_status = status
                    if status == "valid":
                        email.confidence = min(
                            100.0,
                            email.confidence + finding_rules.VERIFICATION_BONUS,
                        )
                    else:
                        email.confidence = min(
                            email.confidence, finding_rules.SYSTEM_CONFIDENCE_CAP
                        )

        if by_address:
            logger.info(
                "[%s] %d adres bulundu (%d yeni).", company.name, len(by_address), new_count
            )
        return len(by_address), new_count

    @staticmethod
    def _merge(address: str, group: List[EmailFinding]) -> EmailFinding:
        """Aynı adrese düşen bulguları tek bulguda birleştirir."""
        best = max(group, key=lambda f: f.confidence)
        source_names = sorted({f.source for f in group})
        confidence = min(
            100.0,
            best.confidence
            + finding_rules.MULTI_SOURCE_BONUS * (len(source_names) - 1),
        )
        # En spesifik tür kazanır; sistem adresleri (noreply vb.) güveni düşürür
        best_type = max(
            (f.type for f in group), key=lambda t: TYPE_WEIGHT.get(t, 1)
        )
        if best_type == "system":
            confidence = min(confidence, finding_rules.SYSTEM_CONFIDENCE_CAP)

        return EmailFinding(
            address=address,
            source=source_names[0],
            sources=source_names,
            confidence=confidence,
            first_name=next((f.first_name for f in group if f.first_name), None),
            last_name=next((f.last_name for f in group if f.last_name), None),
            position=next((f.position for f in group if f.position), None),
            type=best_type,
        )
