# -*- coding: utf-8 -*-
"""Kaynak servisler ile orkestratör arasındaki iç DTO'lar ve ortak kurallar."""

from dataclasses import dataclass, field
from typing import List, Optional

# Kaynak başına temel güven skoru (0..100)
SOURCE_CONFIDENCE = {
    "hunter": 90.0,
    "contact_page": 70.0,
    "crtsh": 55.0,
    "tavily": 50.0,
    "manual": 80.0,
}

# Aynı adres birden çok kaynaktan geldiyse her ek kaynak için bonus
MULTI_SOURCE_BONUS = 5.0

# Doğrulama sonucunun güven skoruna etkisi
VERIFICATION_BONUS = 10.0
SYSTEM_CONFIDENCE_CAP = 25.0

GENERIC_LOCALS = {
    "info",
    "iletisim",
    "contact",
    "destek",
    "support",
    "sales",
    "satis",
    "hr",
    "ik",
    "insankaynaklari",
    "kariyer",
    "careers",
    "jobs",
    "press",
    "basin",
    "pazarlama",
    "marketing",
    "muhasebe",
    "finance",
    "billing",
    "fatura",
    "musterihizmetleri",
    "musteri",
    "operator",
    "central",
}

SYSTEM_LOCALS = {
    "noreply",
    "no-reply",
    "donotreply",
    "do-not-reply",
    "postmaster",
    "webmaster",
    "abuse",
    "root",
    "security",
    "hostmaster",
    "mailmaster",
}


@dataclass
class EmailFinding:
    address: str
    source: str
    sources: List[str] = field(default_factory=list)
    confidence: float = 50.0
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    position: Optional[str] = None
    # personal | generic | system | unknown
    type: str = "unknown"

    def __post_init__(self) -> None:
        if not self.sources:
            self.sources = [self.source]


def classify_email_type(address: str) -> str:
    """Adresin local kısmına göre personal/generic/system sınıflaması."""
    local = address.lower().split("@", 1)[0]
    if local in SYSTEM_LOCALS:
        return "system"
    if any(part in local for part in ("noreply", "no-reply", "donotreply")):
        return "system"
    if local in GENERIC_LOCALS:
        return "generic"
    return "personal"
