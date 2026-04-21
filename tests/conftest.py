"""Pytest fixtures.

Runs every test in STUB mode (no OPENAI_API_KEY), against a temp vector store
so the developer's real index is never touched.
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


@pytest.fixture(scope="function")
def client(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("VECTOR_STORE_PATH", str(tmp_path / "vs"))

    # Reset lru_cache + singletons between tests.
    from app.core import config
    from app.services import llm, vector_store

    config.get_settings.cache_clear()
    llm._singleton = None
    vector_store._store = None

    # Reload the app so cached dependencies are rebuilt.
    import app.main as main
    importlib.reload(main)

    with TestClient(main.app) as c:
        yield c
