# -*- coding: utf-8 -*-
"""Şirket endpoint şemaları."""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


def normalize_domain(value: Optional[str]) -> Optional[str]:
    """Scheme ve www. önekini temizler."""
    if not value:
        return value
    domain = value.strip().lower()
    for prefix in ("https://", "http://"):
        if domain.startswith(prefix):
            domain = domain[len(prefix):]
    domain = domain.split("/", 1)[0]
    return domain.removeprefix("www.")


class CompanyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    category: str = Field(min_length=2, max_length=120)
    domain: Optional[str] = None

    _normalize_domain = field_validator("domain")(lambda v: normalize_domain(v))


class CompanyBulkCreate(BaseModel):
    category: str = Field(min_length=2, max_length=120)
    names: List[str] = Field(min_length=1, max_length=500)
    domain: Optional[str] = None

    _normalize_domain = field_validator("domain")(lambda v: normalize_domain(v))


class CompanyDomainUpdate(BaseModel):
    domain: Optional[str] = None

    _normalize_domain = field_validator("domain")(lambda v: normalize_domain(v))


class CompanyOut(BaseModel):
    id: int
    name: str
    category: str
    domain: Optional[str] = None
    domain_source: Optional[str] = None
    email_count: int = 0

    model_config = {"from_attributes": True}
