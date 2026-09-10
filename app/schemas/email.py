# -*- coding: utf-8 -*-
"""Email endpoint şemaları."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class EmailOut(BaseModel):
    id: int
    address: str
    company_name: Optional[str] = None
    category_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    position: Optional[str] = None
    type: str
    confidence: float
    verification_status: str
    sources: List[str] = []
    first_found_at: datetime
    last_seen_at: datetime


class EmailListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[EmailOut]


class VerifyRequest(BaseModel):
    addresses: List[str] = Field(min_length=1, max_length=100)
    check_deliverability: bool = True


class VerifyResult(BaseModel):
    address: str
    status: str
    verified_address: str


class EmailStatsOut(BaseModel):
    total: int
    valid: int
    invalid: int
    pending: int
    by_type: dict
    by_source: dict


class ApiUsageOut(BaseModel):
    provider: str
    calls: int
    credits_spent: int
