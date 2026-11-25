from surfhub.cache import Cache
from surfhub.utils import hash_dict
from ._body import check_size
from .local import LocalScraper
from .model import MarkdownEngine, Scraper, ScraperResponse, ScraperOptions


class CachedScraper(Scraper):
    def __init__(self, inner: Scraper, cache: Cache):
        self._inner = inner
        self._cache = cache

    @property
    def inner(self) -> Scraper:
        return self._inner

    @property
    def retries(self) -> int:
        return self._inner.retries

    @retries.setter
    def retries(self, value: int):
        self._inner.retries = value

    @property
    def markdown_engine(self) -> MarkdownEngine | None:
        return self._inner.markdown_engine

    @property
    def timeout(self) -> int:
        return self._inner.timeout

    @timeout.setter
    def timeout(self, value: int):
        self._inner.timeout = value

    @property
    def max_bytes(self) -> int:
        return self._inner.max_bytes

    @max_bytes.setter
    def max_bytes(self, value: int):
        self._inner.max_bytes = value

    def _cache_key(self, url: str, options=None, use_browser: bool = False) -> str:
        params = {
            "url": url,
            "provider": self._inner.__class__.__name__,
            "use_browser": use_browser,
        }
        if options:
            params["options"] = options.model_dump()
        if isinstance(self._inner, LocalScraper):
            params["allow_private_network"] = self._inner.allow_private_network
            if not use_browser:
                params["user_agent"] = self._inner.user_agent
        return hash_dict(params)

    def _get_cached(self, key: str) -> ScraperResponse | None:
        cached = self._cache.get(key)
        if cached is not None and 200 <= cached.status_code < 300:
            check_size(len(cached.content), self.max_bytes)
            return cached._with_markdown_engine(self.markdown_engine)
        return None

    def scrape(self, url: str, options: ScraperOptions = None, use_browser: bool = False) -> ScraperResponse:
        key = self._cache_key(url, options, use_browser)
        cached = self._get_cached(key)
        if cached is not None:
            return cached
        result = self._inner.scrape(url, options=options, use_browser=use_browser)
        if 200 <= result.status_code < 300:
            self._cache.set(key, result._with_markdown_engine(None))
        return result

    async def async_scrape(
        self, url: str, options: ScraperOptions = None, use_browser: bool = False
    ) -> ScraperResponse:
        key = self._cache_key(url, options, use_browser)
        cached = self._get_cached(key)
        if cached is not None:
            return cached
        result = await self._inner.async_scrape(url, options=options, use_browser=use_browser)
        if 200 <= result.status_code < 300:
            self._cache.set(key, result._with_markdown_engine(None))
        return result
