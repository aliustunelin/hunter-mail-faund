# -*- coding: utf-8 -*-
"""Liste dışa aktarma endpoint'leri."""

from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.export_service import ExportService

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/bcc")
def export_bcc(
    category: Optional[str] = None,
    only_valid: bool = False,
    include_system: bool = False,
    db: Session = Depends(get_db),
):
    """Virgülle ayrılmış BCC listesi (varsayılan: geçersiz ve sistem adresleri hariç)."""
    content = ExportService(db).bcc_list(
        category=category, only_valid=only_valid, include_system=include_system
    )
    return Response(
        content=content,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="toplu_bcc_listesi.txt"'},
    )


@router.get("/csv")
def export_csv(
    category: Optional[str] = None,
    only_valid: bool = False,
    include_system: bool = False,
    db: Session = Depends(get_db),
):
    content = ExportService(db).csv_content(
        category=category, only_valid=only_valid, include_system=include_system
    )
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="emailler.csv"'},
    )
