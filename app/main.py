# -*- coding: utf-8 -*-
"""Hunter Mail Found — FastAPI uygulaması."""

from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from app.api.v1 import routes_companies, routes_emails, routes_exports, routes_hunt
from app.core.config import get_settings
from app.db.database import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()  # SQLite şemasını kurar + seed verisini yükler (idempotent)
    yield


app = FastAPI(
    title="Hunter Mail Found API",
    description=(
        "Şirket domain'lerinden email toplayan n-tier backend servisi. "
        "Kaynaklar: Hunter.io, crt.sh, iletişim sayfası kazıma, Tavily."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(routes_companies.router)
api_v1.include_router(routes_hunt.router)
api_v1.include_router(routes_emails.router)
api_v1.include_router(routes_exports.router)
app.include_router(api_v1)


@app.get("/health", tags=["meta"])
def health():
    return {
        "status": "ok",
        "hunter_enabled": settings.hunter_enabled,
        "tavily_enabled": settings.tavily_enabled,
    }
