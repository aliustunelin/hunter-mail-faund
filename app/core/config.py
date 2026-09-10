# -*- coding: utf-8 -*-
"""Uygulama ayarları — .env dosyasından okunur."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# .env içindeki yer tutucu değerler: ilgili kaynak sessizce devre dışı kalır.
PLACEHOLDER_VALUES = {
    "",
    "api_key",
    "tavily_api_key_buraya",
    "hunter_api_key_buraya",
    "changeme",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    tavily_api_key: str = ""
    hunter_api_key: str = ""
    database_url: str = "sqlite:///./hunter.db"

    # Harici servislere nazik davranış
    request_timeout_seconds: float = 15.0
    crtsh_timeout_seconds: float = 60.0
    inter_source_delay_seconds: float = 0.4
    inter_company_delay_seconds: float = 1.0

    hunter_domain_limit: int = 25

    @property
    def hunter_enabled(self) -> bool:
        return self.hunter_api_key.strip().lower() not in PLACEHOLDER_VALUES

    @property
    def tavily_enabled(self) -> bool:
        return self.tavily_api_key.strip().lower() not in PLACEHOLDER_VALUES


@lru_cache
def get_settings() -> Settings:
    return Settings()
