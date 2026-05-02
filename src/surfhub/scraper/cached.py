from surfhub.cache import Cache
from surfhub.utils import hash_dict
from .model import Scraper, ScraperResponse, ScraperOptions


class CachedScraper(Scraper):
    def __init__(self, inner: Scraper, cache: Cache):
        self._inner = inner
        self._cache = cache

    @property
    def inner(self) -> Scraper:
        return self._inner

    @property
    def timeout(self) -> int:
        return self._inner.timeout

    @timeout.setter
    def timeout(self, value: int):
        self._inner.timeout = value

    def _cache_key(self, url: str, options=None, use_browser: bool = False) -> str:
        params = {
            "url": url,
            "provider": self._inner.__class__.__name__,
            "use_browser": use_browser,
        }
        if options:
            params["options"] = options.model_dump()
        return hash_dict(params)

    def scrape(self, url: str, options: ScraperOptions = None, use_browser: bool = False) -> ScraperResponse:
        key = self._cache_key(url, options, use_browser)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        result = self._inner.scrape(url, options=options, use_browser=use_browser)
        self._cache.set(key, result)
        return result

    async def async_scrape(
        self, url: str, options: ScraperOptions = None, use_browser: bool = False
    ) -> ScraperResponse:
        key = self._cache_key(url, options, use_browser)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        result = await self._inner.async_scrape(url, options=options, use_browser=use_browser)
        self._cache.set(key, result)
        return result
