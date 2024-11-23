from .model import BaseScrapper
from .local import LocalScrapper
from .browserless import BrowserlessScrapper
from .zyte import ZyteScrapper
from .crawlspace import CrawlspaceScrapper

def get_scrapper(provider=None, api_key=None, **kwargs) -> BaseScrapper:
    if provider == "local":
        return LocalScrapper(api_key=api_key, **kwargs)
    elif provider == "browserless":
        return BrowserlessScrapper(api_key=api_key, **kwargs)
    elif provider == "zyte":
        return ZyteScrapper(api_key=api_key, **kwargs)
    elif provider == "crawlspace":
        return CrawlspaceScrapper(api_key=api_key, **kwargs)

    raise ValueError("Unknown scrapper provider")
