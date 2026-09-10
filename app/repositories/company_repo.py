# -*- coding: utf-8 -*-
"""Şirket/kategori veri erişim katmanı."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.entities import Category, Company


class CompanyRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, category: Optional[str] = None) -> List[Company]:
        stmt = (
            select(Company)
            .options(selectinload(Company.category))
            .order_by(Company.category_id, Company.name)
        )
        if category:
            stmt = stmt.join(Category).where(Category.name == category)
        return list(self.db.scalars(stmt))

    def list_for_hunt(
        self,
        categories: Optional[List[str]] = None,
        names: Optional[List[str]] = None,
    ) -> List[Company]:
        stmt = select(Company).order_by(Company.id)
        if categories:
            stmt = stmt.join(Category).where(Category.name.in_(categories))
        if names:
            stmt = stmt.where(Company.name.in_(names))
        return list(self.db.scalars(stmt))

    def get(self, company_id: int) -> Optional[Company]:
        return self.db.get(Company, company_id)

    def get_by_name(self, name: str) -> Optional[Company]:
        return self.db.scalars(
            select(Company).where(Company.name == name)
        ).first()

    def get_category(self, name: str) -> Optional[Category]:
        return self.db.scalars(
            select(Category).where(Category.name == name)
        ).first()

    def create_category(self, name: str) -> Category:
        category = Category(name=name)
        self.db.add(category)
        self.db.flush()
        return category

    def create(
        self,
        name: str,
        category_id: int,
        domain: Optional[str] = None,
        domain_source: Optional[str] = None,
    ) -> Company:
        company = Company(
            name=name,
            category_id=category_id,
            domain=domain,
            domain_source=domain_source,
        )
        self.db.add(company)
        self.db.flush()
        return company

    def set_domain(self, company: Company, domain: str, source: str) -> None:
        company.domain = domain
        company.domain_source = source
        self.db.flush()
