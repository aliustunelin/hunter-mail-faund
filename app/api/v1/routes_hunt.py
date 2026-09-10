# -*- coding: utf-8 -*-
"""Tarama (hunt) endpoint'leri."""

import json
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.logging import get_logger
from app.repositories.hunt_session_repo import HuntSessionRepository
from app.schemas.hunt import HunterCreditsOut, HuntRunRequest, HuntSessionOut
from app.services.hunt_runner import run_hunt_in_background
from app.services.hunt_service import ALL_SOURCES, HuntService
from app.services.sources.hunter_source import HunterSource

logger = get_logger(__name__)

router = APIRouter(prefix="/hunt", tags=["hunt"])


@router.post("/run", response_model=HuntSessionOut, status_code=202)
def run_hunt(
    payload: HuntRunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Yeni tarama başlatır ve arka planda çalıştırır.

    Aynı anda tek tarama çalışabilir; kapsamı `categories` / `companies`
    ile, kaynakları `sources` + `use_hunter` ile daraltabilirsiniz.
    """
    session_repo = HuntSessionRepository(db)
    if session_repo.get_running():
        raise HTTPException(status_code=409, detail="Zaten calisan bir tarama var.")

    sources = [s for s in payload.sources if s in ALL_SOURCES]
    if payload.use_hunter and "hunter" not in sources:
        sources.append("hunter")
    if not sources:
        raise HTTPException(
            status_code=400,
            detail=f"Gecerli kaynak yok. Secenekler: {', '.join(ALL_SOURCES)}",
        )

    params = {
        "categories": payload.categories,
        "company_names": payload.companies,
        "sources": sources,
        "resolve_missing_domains": payload.resolve_missing_domains,
        "verify_emails": payload.verify_emails,
    }
    hunt_session = session_repo.create(json.dumps(params, ensure_ascii=False))
    db.commit()

    background_tasks.add_task(run_hunt_in_background, hunt_session.id, params)
    logger.info("Tarama oturumu #%s kuyruga alindi.", hunt_session.id)
    return HuntSessionOut.from_entity(hunt_session)


@router.get("/sessions", response_model=List[HuntSessionOut])
def list_sessions(limit: int = 20, db: Session = Depends(get_db)):
    sessions = HuntSessionRepository(db).list(limit=limit)
    return [HuntSessionOut.from_entity(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=HuntSessionOut)
def get_session(session_id: int, db: Session = Depends(get_db)):
    hunt_session = HuntSessionRepository(db).get(session_id)
    if hunt_session is None:
        raise HTTPException(status_code=404, detail="Tarama oturumu bulunamadi.")
    return HuntSessionOut.from_entity(hunt_session)


@router.get("/sources")
def list_sources(db: Session = Depends(get_db)):
    return {
        "all": ALL_SOURCES,
        "default": ["crtsh", "contact_page", "tavily"],
    }


@router.get("/credits/hunter", response_model=HunterCreditsOut)
def hunter_credits(db: Session = Depends(get_db)):
    """Hunter hesabındaki kalan krediyi gösterir."""
    hunter = HunterSource(db)
    if not hunter.settings.hunter_enabled:
        return HunterCreditsOut(enabled=False, credits_left=None)
    return HunterCreditsOut(enabled=True, credits_left=hunter.credits_left())
