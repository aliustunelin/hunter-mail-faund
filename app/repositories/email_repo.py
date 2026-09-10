# -*- coding: utf-8 -*-
"""Email veri erişim katmanı."""

from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Tuple

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.entities import Category, Company, Email, EmailSource
from app.services.findings import EmailFinding


class EmailRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_address(self, address: str) -> Optional[Email]:
        return self.db.scalars(
            select(Email).where(Email.address == address.lower().strip())
        ).first()

    def get(self, email_id: int) -> Optional[Email]:
        return self.db.get(Email, email_id)

    def add_sources_if_missing(
        self, email_id: int, sources: Iterable[str]
    ) -> None:
        existing = set(
            self.db.scalars(
                select(EmailSource.source).where(EmailSource.email_id == email_id)
            ).all()
        )
        for source in sources:
            if source not in existing:
                self.db.add(EmailSource(email_id=email_id, source=source))

    def upsert_finding(
        self, company: Optional[Company], finding: EmailFinding
    ) -> Tuple[Email, bool]:
        """Bulgunun adresi kayıtlıysa güncelleştirir, değilse ekler. (email, is_new) döner."""
        address = finding.address.lower().strip()
        email = self.get_by_address(address)
        is_new = email is None
        if is_new:
            email = Email(
                company_id=company.id if company else None,
                address=address,
                first_name=finding.first_name,
                last_name=finding.last_name,
                position=finding.position,
                type=finding.type,
                confidence=finding.confidence,
            )
            self.db.add(email)
            self.db.flush()
        else:
            email.last_seen_at = datetime.now(timezone.utc)
            if finding.confidence > email.confidence:
                email.confidence = finding.confidence
            if email.first_name is None and finding.first_name:
                email.first_name = finding.first_name
            if email.last_name is None and finding.last_name:
                email.last_name = finding.last_name
            if email.position is None and finding.position:
                email.position = finding.position
            if email.type in ("unknown", None) and finding.type != "unknown":
                email.type = finding.type
            if email.company_id is None and company is not None:
                email.company_id = company.id
        self.add_sources_if_missing(email.id, finding.sources or [finding.source])
        return email, is_new

    def list(
        self,
        category: Optional[str] = None,
        company_id: Optional[int] = None,
        source: Optional[str] = None,
        verification_status: Optional[str] = None,
        email_type: Optional[str] = None,
        q: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Tuple[Email, Optional[Company], Optional[Category]]], int]:
        stmt = (
            select(Email, Company, Category)
            .join(Company, Email.company_id == Company.id, isouter=True)
            .join(Category, Company.category_id == Category.id, isouter=True)
            .options(selectinload(Email.sources))
        )
        filters: List[ColumnElement] = []
        if category:
            filters.append(Category.name == category)
        if company_id:
            filters.append(Email.company_id == company_id)
        if verification_status:
            filters.append(Email.verification_status == verification_status)
        if email_type:
            filters.append(Email.type == email_type)
        if q:
            filters.append(Email.address.contains(q.lower()))
        if filters:
            stmt = stmt.where(*filters)
        if source:
            stmt = stmt.where(
                Email.id.in_(
                    select(EmailSource.email_id).where(EmailSource.source == source)
                )
            )
        total = self.db.scalar(
            select(func.count()).select_from(stmt.order_by(None).subquery())
        )
        rows = list(
            self.db.execute(
                stmt.order_by(Email.confidence.desc(), Email.address)
                .limit(limit)
                .offset(offset)
            )
        )
        return rows, int(total or 0)

    def export_addresses(
        self,
        category: Optional[str] = None,
        only_valid: bool = False,
        include_system: bool = False,
    ) -> List[str]:
        stmt = (
            select(Email.address)
            .join(Company, Email.company_id == Company.id, isouter=True)
            .join(Category, Company.category_id == Category.id, isouter=True)
            .order_by(Email.address)
        )
        if category:
            stmt = stmt.where(Category.name == category)
        if only_valid:
            stmt = stmt.where(Email.verification_status == "valid")
        else:
            stmt = stmt.where(Email.verification_status != "invalid")
        if not include_system:
            stmt = stmt.where(Email.type != "system")
        return [row[0] for row in self.db.execute(stmt)]

    def export_rows(
        self,
        category: Optional[str] = None,
        only_valid: bool = False,
        include_system: bool = False,
    ) -> List[Tuple]:
        stmt = (
            select(
                Email.address,
                Company.name,
                Category.name,
                Email.position,
                Email.type,
                Email.confidence,
                Email.verification_status,
                func.group_concat(EmailSource.source, "|"),
                Email.first_found_at,
            )
            .join(Company, Email.company_id == Company.id, isouter=True)
            .join(Category, Company.category_id == Category.id, isouter=True)
            .join(EmailSource, EmailSource.email_id == Email.id, isouter=True)
            .group_by(Email.id)
            .order_by(Email.address)
        )
        if category:
            stmt = stmt.where(Category.name == category)
        if only_valid:
            stmt = stmt.where(Email.verification_status == "valid")
        else:
            stmt = stmt.where(Email.verification_status != "invalid")
        if not include_system:
            stmt = stmt.where(Email.type != "system")
        return list(self.db.execute(stmt))

    def counts_by_company(self) -> Dict[int, int]:
        rows = self.db.execute(
            select(Email.company_id, func.count(Email.id))
            .where(Email.company_id.is_not(None))
            .group_by(Email.company_id)
        ).all()
        return {company_id: count for company_id, count in rows}

    def stats(self) -> Dict[str, object]:
        by_status = dict(
            self.db.execute(
                select(Email.verification_status, func.count(Email.id)).group_by(
                    Email.verification_status
                )
            ).all()
        )
        by_type = dict(
            self.db.execute(
                select(Email.type, func.count(Email.id)).group_by(Email.type)
            ).all()
        )
        by_source = dict(
            self.db.execute(
                select(EmailSource.source, func.count(EmailSource.email_id)).group_by(
                    EmailSource.source
                )
            ).all()
        )
        total = int(self.db.scalar(select(func.count(Email.id))) or 0)
        return {
            "total": total,
            "valid": int(by_status.get("valid", 0)),
            "invalid": int(by_status.get("invalid", 0)),
            "pending": int(by_status.get("pending", 0)),
            "by_type": by_type,
            "by_source": by_source,
        }
