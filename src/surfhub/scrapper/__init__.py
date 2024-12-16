from .model import BaseScrapper
from .local import LocalScrapper
from .browserless import BrowserlessScrapper
from .zyte import ZyteScrapper
from .crawlbase import CrawlbaseScrapper

def get_scrapper(provider=None, api_key=None, **kwargs) -> BaseScrapper:
    if provider == "local":
        return LocalScrapper(**kwargs)
    elif provider == "browserless":
        return BrowserlessScrapper(api_key=api_key, **kwargs)
    elif provider == "zyte":
        return ZyteScrapper(api_key=api_key, **kwargs)
    elif provider == "crawlbase":
        return CrawlbaseScrapper(api_key=api_key, **kwargs)

    raise ValueError("Unknown scrapper provider")
