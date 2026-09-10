# -*- coding: utf-8 -*-
"""Email endpoint'leri."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.api_usage_repo import ApiUsageRepository
from app.repositories.email_repo import EmailRepository
from app.schemas.email import (
    ApiUsageOut,
    EmailListResponse,
    EmailOut,
    EmailStatsOut,
    VerifyRequest,
    VerifyResult,
)
from app.services.email_verifier import EmailVerifier
from app.services.findings import VERIFICATION_BONUS, SYSTEM_CONFIDENCE_CAP

router = APIRouter(tags=["emails"])


@router.get("/emails", response_model=EmailListResponse)
def list_emails(
    category: Optional[str] = None,
    company_id: Optional[int] = None,
    source: Optional[str] = None,
    verification_status: Optional[str] = None,
    email_type: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    rows, total = EmailRepository(db).list(
        category=category,
        company_id=company_id,
        source=source,
        verification_status=verification_status,
        email_type=email_type,
        q=q,
        limit=limit,
        offset=offset,
    )
    items = [
        EmailOut(
            id=email.id,
            address=email.address,
            company_name=company.name if company else None,
            category_name=category.name if category else None,
            first_name=email.first_name,
            last_name=email.last_name,
            position=email.position,
            type=email.type,
            confidence=email.confidence,
            verification_status=email.verification_status,
            sources=[s.source for s in email.sources],
            first_found_at=email.first_found_at,
            last_seen_at=email.last_seen_at,
        )
        for email, company, category in rows
    ]
    return EmailListResponse(total=total, limit=limit, offset=offset, items=items)


@router.post("/emails/verify", response_model=list[VerifyResult])
def verify_emails(payload: VerifyRequest, db: Session = Depends(get_db)):
    """Adresleri sözdizimi + MX açısından doğrular; kayıtlıysa durumunu günceller."""
    verifier = EmailVerifier()
    repo = EmailRepository(db)
    results = []
    for address in payload.addresses:
        status, verified = verifier.verify(address, payload.check_deliverability)
        email = repo.get_by_address(address)
        if email is not None:
            email.verification_status = status
            if status == "valid":
                email.confidence = min(100.0, email.confidence + VERIFICATION_BONUS)
            else:
                email.confidence = min(email.confidence, SYSTEM_CONFIDENCE_CAP)
        results.append(
            VerifyResult(address=address, status=status, verified_address=verified)
        )
    db.commit()
    return results


@router.get("/emails/stats", response_model=EmailStatsOut)
def email_stats(db: Session = Depends(get_db)):
    stats = EmailRepository(db).stats()
    return EmailStatsOut(**stats)


@router.get("/usage", response_model=list[ApiUsageOut])
def api_usage(db: Session = Depends(get_db)):
    return [ApiUsageOut(**row) for row in ApiUsageRepository(db).summary()]
