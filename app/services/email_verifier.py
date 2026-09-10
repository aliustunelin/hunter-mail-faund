# -*- coding: utf-8 -*-
"""Sözdizimi + MX tabanlı email doğrulama (email-validator sarmalayıcı)."""

from typing import Tuple

from email_validator import EmailNotValidError, validate_email

from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailVerifier:
    """Adresi doğrular; ('valid'|'invalid', normalize_edilmis_adres) döner.

    check_deliverability=True iken DNS/MX sorgusu da yapılır (ağ erişimi gerekir).
    """

    def verify(
        self, address: str, check_deliverability: bool = True
    ) -> Tuple[str, str]:
        try:
            result = validate_email(
                address, check_deliverability=check_deliverability
            )
            normalized = result.ascii_email or result.email
            return "valid", normalized.lower()
        except EmailNotValidError as exc:
            logger.debug("Dogrulama basarisiz (%s): %s", address, exc)
            return "invalid", address.lower()
