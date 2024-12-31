from .model import Scraper
from .local import LocalScraper
from .browserless import BrowserlessScraper
from .zyte import ZyteScraper
from .crawlbase import CrawlbaseScraper

def get_scraper(provider, api_key=None, **kwargs) -> Scraper:
    if provider == "local":
        return LocalScraper(**kwargs)
    elif provider == "browserless":
        return BrowserlessScraper(api_key=api_key, **kwargs)
    elif provider == "zyte":
        return ZyteScraper(api_key=api_key, **kwargs)
    elif provider == "crawlbase":
        return CrawlbaseScraper(api_key=api_key, **kwargs)

    raise ValueError("Unknown scraper provider")
