# -*- coding: utf-8 -*-
"""Ortak FastAPI bağımlılıkları."""

from app.db.database import get_db  # re-export

__all__ = ["get_db"]
