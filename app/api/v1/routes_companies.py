# -*- coding: utf-8 -*-
"""Şirket endpoint'leri (sunum katmanı)."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.company_repo import CompanyRepository
from app.repositories.email_repo import EmailRepository
from app.schemas.company import (
    CompanyBulkCreate,
    CompanyCreate,
    CompanyDomainUpdate,
    CompanyOut,
)

router = APIRouter(prefix="/companies", tags=["companies"])


def _to_out(db: Session, company) -> CompanyOut:
    counts = EmailRepository(db).counts_by_company()
    return CompanyOut(
        id=company.id,
        name=company.name,
        category=company.category.name,
        domain=company.domain,
        domain_source=company.domain_source,
        email_count=counts.get(company.id, 0),
    )


@router.get("", response_model=List[CompanyOut])
def list_companies(category: str = None, db: Session = Depends(get_db)):
    companies = CompanyRepository(db).list(category=category)
    return [_to_out(db, company) for company in companies]


@router.post("", response_model=CompanyOut, status_code=201)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    repo = CompanyRepository(db)
    if repo.get_by_name(payload.name):
        raise HTTPException(status_code=409, detail="Sirket zaten kayitli.")
    category = repo.get_category(payload.category) or repo.create_category(
        payload.category
    )
    company = repo.create(
        payload.name,
        category.id,
        domain=payload.domain,
        domain_source="manual" if payload.domain else None,
    )
    db.commit()
    db.refresh(company)
    return _to_out(db, company)


@router.patch("/{company_id}/domain", response_model=CompanyOut)
def update_company_domain(
    company_id: int, payload: CompanyDomainUpdate, db: Session = Depends(get_db)
):
    """Şirketin domain'ini elle ayarlar (Tavily kredisi harcamadan tarama için)."""
    repo = CompanyRepository(db)
    company = repo.get(company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Sirket bulunamadi.")
    repo.set_domain(company, payload.domain, "manual" if payload.domain else None)
    db.commit()
    db.refresh(company)
    return _to_out(db, company)


@router.post("/bulk", response_model=List[CompanyOut], status_code=201)
def create_companies_bulk(payload: CompanyBulkCreate, db: Session = Depends(get_db)):
    repo = CompanyRepository(db)
    category = repo.get_category(payload.category) or repo.create_category(
        payload.category
    )
    created = []
    for name in payload.names:
        name = name.strip()
        if not name or repo.get_by_name(name):
            continue
        company = repo.create(
            name,
            category.id,
            domain=payload.domain,
            domain_source="manual" if payload.domain else None,
        )
        created.append(company)
    db.commit()
    return [_to_out(db, company) for company in created]
