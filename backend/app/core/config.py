"""Runtime configuration loaded from env vars."""
from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o-mini"
    openai_embed_model: str = "text-embedding-3-small"

    # Optional: Tavily Search API key. Used ONLY as a last-resort fallback
    # when the headless-Chromium Brave path returns no results (usually
    # because Brave is serving a PoW captcha). Get a free key at
    # https://tavily.com (1000 searches/month).
    tavily_api_key: str = ""

    vector_store_path: str = "./data/vector_store"
    chunk_size: int = 800
    chunk_overlap: int = 120
    top_k: int = 4
    request_timeout: int = 30

    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
