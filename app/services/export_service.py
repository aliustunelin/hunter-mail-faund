# -*- coding: utf-8 -*-
"""Toplu e-posta listesi (BCC) ve CSV üretimi."""

import csv
import io
from typing import List, Optional

from sqlalchemy.orm import Session

from app.repositories.email_repo import EmailRepository

CSV_HEADERS = [
    "address",
    "company",
    "category",
    "position",
    "type",
    "confidence",
    "verification_status",
    "sources",
    "first_found_at",
]


class ExportService:
    def __init__(self, db: Session):
        self.email_repo = EmailRepository(db)

    def bcc_list(
        self,
        category: Optional[str] = None,
        only_valid: bool = False,
        include_system: bool = False,
    ) -> str:
        addresses: List[str] = self.email_repo.export_addresses(
            category=category, only_valid=only_valid, include_system=include_system
        )
        return ", ".join(addresses)

    def csv_content(
        self,
        category: Optional[str] = None,
        only_valid: bool = False,
        include_system: bool = False,
    ) -> str:
        rows = self.email_repo.export_rows(
            category=category, only_valid=only_valid, include_system=include_system
        )
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(CSV_HEADERS)
        for row in rows:
            writer.writerow(
                [
                    row[0],
                    row[1] or "",
                    row[2] or "",
                    row[3] or "",
                    row[4] or "",
                    row[5],
                    row[6],
                    (row[7] or "").replace("|", ", "),
                    row[8].isoformat() if row[8] else "",
                ]
            )
        return buffer.getvalue()
