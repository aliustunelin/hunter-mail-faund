# -*- coding: utf-8 -*-
"""SQLAlchemy ORM varlıkları (veri katmanı)."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)

    companies: Mapped[List["Company"]] = relationship(back_populates="category")


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    domain: Mapped[Optional[str]] = mapped_column(String(200), index=True)
    domain_source: Mapped[Optional[str]] = mapped_column(String(50))  # tavily | manual
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    category: Mapped["Category"] = relationship(back_populates="companies")
    emails: Mapped[List["Email"]] = relationship(back_populates="company")


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("companies.id"), index=True
    )
    address: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    position: Mapped[Optional[str]] = mapped_column(String(200))
    # personal | generic | system | unknown
    type: Mapped[str] = mapped_column(String(20), default="unknown")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)  # 0..100
    # pending | valid | invalid
    verification_status: Mapped[str] = mapped_column(String(20), default="pending")
    first_found_at: Mapped[datetime] = mapped_column(default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(default=utcnow)

    company: Mapped[Optional["Company"]] = relationship(back_populates="emails")
    sources: Mapped[List["EmailSource"]] = relationship(back_populates="email")


class EmailSource(Base):
    __tablename__ = "email_sources"
    __table_args__ = (
        UniqueConstraint("email_id", "source", name="uq_email_source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email_id: Mapped[int] = mapped_column(ForeignKey("emails.id"), index=True)
    # hunter | crtsh | contact_page | tavily | manual
    source: Mapped[str] = mapped_column(String(50))
    found_at: Mapped[datetime] = mapped_column(default=utcnow)

    email: Mapped["Email"] = relationship(back_populates="sources")


class HuntSession(Base):
    __tablename__ = "hunt_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    # running | completed | failed
    status: Mapped[str] = mapped_column(String(20), default="running")
    params_json: Mapped[Optional[str]] = mapped_column(Text)
    companies_scanned: Mapped[int] = mapped_column(Integer, default=0)
    emails_found: Mapped[int] = mapped_column(Integer, default=0)
    new_emails: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(default=utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)


class ApiUsage(Base):
    __tablename__ = "api_usage"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(50))  # hunter | tavily
    endpoint: Mapped[str] = mapped_column(String(200))
    credits_spent: Mapped[int] = mapped_column(Integer, default=0)
    called_at: Mapped[datetime] = mapped_column(default=utcnow)
