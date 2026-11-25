import sqlite3

import pytest

from surfhub.cache import FileCache
from surfhub.scraper.model import ScraperResponse
from surfhub.serper.tavily import TavilySerpResponse


def test_file_cache_round_trips_responses(tmp_path):
    cache = FileCache(tmp_path)
    response = ScraperResponse(content=b"\xff\x00", status_code=200, final_url="https://example.com")
    serp = TavilySerpResponse(items=[], cached=False, answer="Answer")
    cache.set("page", response)
    cache.set("search", serp)

    reopened = FileCache(tmp_path)
    assert reopened.get("page") == response
    assert reopened.get("search") == serp
    reopened.delete("page")
    assert reopened.get("page") is None
    reopened.clear()
    assert reopened.get("search") is None


def test_file_cache_ignores_legacy_and_malformed_records(tmp_path):
    legacy = tmp_path / "cache.db"
    legacy.write_bytes(b"previous cache")
    cache = FileCache(tmp_path)
    assert cache.get("legacy") is None
    assert legacy.read_bytes() == b"previous cache"
    with sqlite3.connect(tmp_path / "surfhub-cache.sqlite3") as db:
        db.execute("INSERT INTO entries VALUES (?, ?, ?, ?)", ("invalid", "ScraperResponse", "{}", 1e12))
    assert cache.get("invalid") is None
    with pytest.raises(TypeError):
        cache.set("unsupported", object())
