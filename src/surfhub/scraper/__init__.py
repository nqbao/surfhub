from .model import Scraper
from .local import LocalScraper
from .browserless import BrowserlessScraper
from .zyte import ZyteScraper
from .crawlbase import CrawlbaseScraper
from .exa import ExaScraper
from .jina import JinaScraper
from .firecrawl import FirecrawlScraper
from .scrapingbee import ScrapingBeeScraper
from .cached import CachedScraper
from surfhub.cache.base import Cache


def get_scraper(provider, api_key=None, cache: Cache = None, **kwargs) -> Scraper:
    if provider == "local":
        scraper = LocalScraper(**kwargs)
    elif provider == "browserless":
        scraper = BrowserlessScraper(api_key=api_key, **kwargs)
    elif provider == "zyte":
        scraper = ZyteScraper(api_key=api_key, **kwargs)
    elif provider == "crawlbase":
        scraper = CrawlbaseScraper(api_key=api_key, **kwargs)
    elif provider == "exa":
        scraper = ExaScraper(api_key=api_key, **kwargs)
    elif provider == "jina":
        scraper = JinaScraper(api_key=api_key, **kwargs)
    elif provider == "firecrawl":
        scraper = FirecrawlScraper(api_key=api_key, **kwargs)
    elif provider == "scrapingbee":
        scraper = ScrapingBeeScraper(api_key=api_key, **kwargs)
    else:
        raise ValueError("Unknown scraper provider")

    if cache:
        return CachedScraper(scraper, cache)
    return scraper
