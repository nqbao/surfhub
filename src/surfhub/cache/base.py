import base64
import json
import sqlite3
import time
from contextlib import closing
from functools import lru_cache
from pathlib import Path

__all__ = ["Cache", "DummyCache", "FileCache"]


class Cache:
    def get(self, key: str):
        raise NotImplementedError()

    def set(self, key: str, value, ttl: int = None):
        raise NotImplementedError()

    def has(self, key: str) -> bool:
        return self.get(key) is not None

    def delete(self, key: str):
        raise NotImplementedError()

    def clear(self):
        raise NotImplementedError()


class DummyCache(Cache):
    def get(self, key: str):
        return None

    def set(self, key: str, value, ttl: int = None):
        return None

    def delete(self, key: str):
        return None

    def clear(self):
        return None


class FileCache(Cache):
    """Store JSON values, bytes, and Surfhub responses in a local cache directory."""

    def __init__(self, cache_dir: str, default_ttl: int = 3600):
        directory = Path(cache_dir)
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        self._database = directory / "surfhub-cache.sqlite3"
        self.ttl = default_ttl
        with closing(sqlite3.connect(self._database)) as db, db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS entries "
                "(key TEXT PRIMARY KEY, kind TEXT NOT NULL, data TEXT NOT NULL, expires REAL NOT NULL)"
            )
            db.execute("CREATE INDEX IF NOT EXISTS entries_expires ON entries(expires)")

    def get(self, key: str):
        with closing(sqlite3.connect(self._database)) as db:
            entry = db.execute(
                "SELECT kind, data FROM entries WHERE key = ? AND expires > ?", (key, time.time())
            ).fetchone()
        if entry is None:
            return None
        kind, data = entry
        try:
            value = json.loads(data)
            if kind == "json":
                return value
            if kind == "bytes":
                return base64.b64decode(value, validate=True)
            model = _response_types().get(kind)
            if model is not None:
                if kind == "ScraperResponse":
                    value["content"] = base64.b64decode(value["content"], validate=True)
                return model.model_validate(value)
        except (KeyError, TypeError, ValueError):
            return None
        return None

    def set(self, key: str, value, ttl: int = None):
        kind = "json"
        if isinstance(value, bytes):
            kind = "bytes"
            value = base64.b64encode(value).decode("ascii")
        else:
            name = type(value).__name__
            if type(value) is _response_types().get(name):
                kind = name
                if kind == "ScraperResponse":
                    value = value.model_dump()
                    value["content"] = base64.b64encode(value["content"]).decode("ascii")
                else:
                    value = value.model_dump(mode="json")
        data = json.dumps(value)
        now = time.time()
        with closing(sqlite3.connect(self._database)) as db, db:
            db.execute("DELETE FROM entries WHERE expires <= ?", (now,))
            db.execute(
                "INSERT OR REPLACE INTO entries VALUES (?, ?, ?, ?)", (key, kind, data, now + (ttl or self.ttl))
            )

    def delete(self, key: str):
        with closing(sqlite3.connect(self._database)) as db, db:
            db.execute("DELETE FROM entries WHERE key = ?", (key,))

    def clear(self):
        with closing(sqlite3.connect(self._database)) as db, db:
            db.execute("DELETE FROM entries")


@lru_cache(maxsize=1)
def _response_types():
    from surfhub.scraper.model import ScraperResponse
    from surfhub.serper.model import DuckDuckGoSerpResponse, SerpResponse
    from surfhub.serper.perplexity import PerplexitySerpResponse
    from surfhub.serper.tavily import TavilySerpResponse

    return {
        model.__name__: model
        for model in (ScraperResponse, DuckDuckGoSerpResponse, SerpResponse, PerplexitySerpResponse, TavilySerpResponse)
    }
