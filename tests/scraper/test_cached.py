import httpx
import pytest
import respx
from surfhub.cache.base import Cache
from surfhub.scraper.local import LocalScraper
from surfhub.scraper.cached import CachedScraper
from surfhub.scraper import get_scraper
from surfhub.scraper.model import ScraperResponse
from surfhub.errors import ScrapingError


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


class TestCachedScraper:
    @pytest.mark.anyio
    async def test_shared_cache_uses_the_calling_scrapers_markdown_engine(self):
        cache = DictCache()
        url = "https://example.com"
        first = get_scraper("local", cache=cache, markdown_engine=lambda _: "# First")
        second = get_scraper("local", cache=cache, markdown_engine=lambda _: "# Second")

        with respx.mock:
            route = respx.get(url).respond(200, headers={"Content-Type": "text/html"}, text="<h1>Page</h1>")
            first_page = first.scrape(url)
            second_page = await second.async_scrape(url)

        assert first_page.markdown() == "# First"
        assert second_page.markdown() == "# Second"
        assert route.call_count == 1

    @pytest.mark.anyio
    async def test_old_and_new_errors_are_not_served_from_cache(self):
        cache = DictCache()
        scraper = get_scraper("local", cache=cache)
        scraper.retries = 1
        assert scraper.inner.retries == 1
        url = "https://example.com"
        key = scraper._cache_key(url)
        old_error = ScraperResponse(content=b"old error", status_code=503, final_url=url)
        cache.set(key, old_error)

        with respx.mock:
            route = respx.get(url).mock(side_effect=[httpx.Response(429), httpx.Response(200)])
            with pytest.raises(ScrapingError):
                scraper.scrape(url)
            assert cache.get(key) == old_error
            assert (await scraper.async_scrape(url)).status_code == 200
            assert scraper.scrape(url).status_code == 200
            assert route.call_count == 2

    def test_cache_miss_fetches_and_caches(self):
        cache = DictCache()
        inner = LocalScraper()
        cached = CachedScraper(inner, cache)

        with respx.mock:
            respx.get("https://example.com").mock(
                return_value=httpx.Response(200, text="<html>hello</html>"),
            )
            result = cached.scrape("https://example.com")

        assert result.content.decode() == "<html>hello</html>"
        assert result.status_code == 200
        assert cache._store

    def test_cache_hit_returns_cached(self):
        cache = DictCache()
        inner = LocalScraper()
        cached = CachedScraper(inner, cache)

        key = cached._cache_key("https://example.com")
        pre_cached = ScraperResponse(
            content=b"<html>cached</html>",
            content_type="text/html",
            final_url="https://example.com",
            status_code=200,
        )
        cache.set(key, pre_cached)

        result = cached.scrape("https://example.com")
        assert result.content.decode() == "<html>cached</html>"

    def test_cache_key_varies_by_url(self):
        cache = DictCache()
        inner = LocalScraper()
        cached = CachedScraper(inner, cache)

        key1 = cached._cache_key("https://example.com")
        key2 = cached._cache_key("https://other.com")
        assert key1 != key2

    def test_cache_key_varies_by_use_browser(self):
        cache = DictCache()
        inner = LocalScraper()
        cached = CachedScraper(inner, cache)

        key1 = cached._cache_key("https://example.com", use_browser=False)
        key2 = cached._cache_key("https://example.com", use_browser=True)
        assert key1 != key2

    def test_custom_user_agent_has_its_own_cached_response(self):
        cache = DictCache()
        url = "https://example.com"
        default = get_scraper("local", cache=cache)
        custom = get_scraper("local", cache=cache, user_agent="ResearchAgent/1.0")

        with respx.mock:
            route = respx.get(url).mock(side_effect=[httpx.Response(403), httpx.Response(200)])
            with pytest.raises(ScrapingError):
                default.scrape(url)
            assert custom.scrape(url).status_code == 200
            assert custom.scrape(url).status_code == 200
            assert route.call_count == 2

    def test_factory_with_cache_returns_cached_scraper(self):
        cache = DictCache()
        scraper = get_scraper("local", cache=cache)
        assert isinstance(scraper, CachedScraper)
        assert isinstance(scraper.inner, LocalScraper)

    def test_factory_without_cache_returns_plain_scraper(self):
        scraper = get_scraper("local")
        assert isinstance(scraper, LocalScraper)
        assert not isinstance(scraper, CachedScraper)

    def test_second_call_hits_cache(self):
        cache = DictCache()
        inner = LocalScraper()
        cached = CachedScraper(inner, cache)

        with respx.mock:
            route = respx.get("https://example.com").mock(
                return_value=httpx.Response(200, text="<html>fresh</html>"),
            )
            result1 = cached.scrape("https://example.com")

        result2 = cached.scrape("https://example.com")
        assert result1.content == result2.content
        assert result1.content.decode() == "<html>fresh</html>"
        assert result1.content.decode() == result2.content.decode()

    def test_timeout_delegates_to_inner(self):
        cache = DictCache()
        inner = LocalScraper()
        inner.timeout = 42
        cached = CachedScraper(inner, cache)
        assert cached.timeout == 42

        cached.timeout = 99
        assert inner.timeout == 99

    @pytest.mark.anyio
    async def test_async_cache_miss_and_hit(self):
        cache = DictCache()
        inner = LocalScraper()
        cached = CachedScraper(inner, cache)

        with respx.mock:
            respx.get("https://example.com").mock(
                return_value=httpx.Response(200, text="<html>async fresh</html>"),
            )
            result1 = await cached.async_scrape("https://example.com")

        result2 = await cached.async_scrape("https://example.com")
        assert result1.content == result2.content
        assert result1.content.decode() == "<html>async fresh</html>"
