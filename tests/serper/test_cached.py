import httpx
import pytest
import respx
from surfhub.cache.base import Cache
from surfhub.serper.model import SerpResponse, SerpResult
from surfhub.serper.serpapi import SerpApi
from surfhub.serper.cached import CachedSerper
from surfhub.serper import get_serper
from surfhub.cache import FileCache


class DictCache(Cache):
    def __init__(self):
        self._store = {}

    def get(self, key):
        return self._store.get(key)

    def set(self, key, value, ttl=None):
        self._store[key] = value

    def delete(self, key):
        self._store.pop(key, None)

    def clear(self):
        self._store.clear()


def mock_serp_response(items=None):
    return httpx.Response(
        200,
        json={
            "search_metadata": {"status": "Success"},
            "organic_results": [
                {
                    "title": "Example",
                    "link": "https://example.com",
                    "snippet": "A snippet",
                    "displayed_link": "example.com",
                }
            ],
        },
    )


class TestCachedSerper:
    def test_cache_miss_fetches_and_caches(self):
        cache = DictCache()
        inner = SerpApi(api_key="test")
        cached = CachedSerper(inner, cache)

        with respx.mock:
            respx.get("https://serpapi.com/search").mock(return_value=mock_serp_response())
            result = cached.serp("test query")

        assert len(result.items) == 1
        assert result.cached is False
        assert cache._store

    def test_cache_hit_returns_cached(self):
        cache = DictCache()
        inner = SerpApi(api_key="test")
        cached = CachedSerper(inner, cache)

        key = cached._cache_key("test query", None, None, None)
        pre_cached = SerpResponse(
            items=[SerpResult(title="Cached", link="https://cached.com", snippet="...", prefix="")],
            cached=False,
        )
        cache.set(key, pre_cached)

        result = cached.serp("test query")
        assert result.items[0].title == "Cached"
        assert result.cached is True

    def test_cache_key_varies_by_query(self):
        cache = DictCache()
        inner = SerpApi(api_key="test")
        cached = CachedSerper(inner, cache)

        key1 = cached._cache_key("hello", None, None, None)
        key2 = cached._cache_key("world", None, None, None)
        assert key1 != key2

    def test_factory_with_cache_returns_cached_serper(self):
        cache = DictCache()
        serper = get_serper("serpapi", api_key="test", cache=cache)
        assert isinstance(serper, CachedSerper)
        assert isinstance(serper.inner, SerpApi)

    def test_factory_without_cache_returns_plain_serper(self):
        serper = get_serper("serpapi", api_key="test")
        assert isinstance(serper, SerpApi)
        assert not isinstance(serper, CachedSerper)

    def test_second_call_hits_cache(self):
        cache = DictCache()
        inner = SerpApi(api_key="test")
        cached = CachedSerper(inner, cache)

        with respx.mock:
            route = respx.get("https://serpapi.com/search").mock(return_value=mock_serp_response())
            result1 = cached.serp("test query")

        result2 = cached.serp("test query")
        assert result1.items[0].title == result2.items[0].title
        assert result1.cached is False
        assert result2.cached is True

    @pytest.mark.anyio
    async def test_async_cache_miss_and_hit(self):
        cache = DictCache()
        inner = SerpApi(api_key="test")
        cached = CachedSerper(inner, cache)

        with respx.mock:
            respx.get("https://serpapi.com/search").mock(return_value=mock_serp_response())
            result1 = await cached.async_serp("async query")

        result2 = await cached.async_serp("async query")
        assert result1.cached is False
        assert result2.cached is True
