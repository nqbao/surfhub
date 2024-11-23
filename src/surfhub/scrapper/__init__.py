from .local import LocalScrapper
from .browserless import BrowserlessScrapper
from .zyte import ZyteScrapper

def get_scrapper(provider=None, api_key=None):
    if provider == "local":
        return LocalScrapper(api_key=api_key)
    elif provider == "browserless":
        return BrowserlessScrapper(api_key=api_key)
    elif provider == "zyte":
        return ZyteScrapper(api_key=api_key)

    raise ValueError("Unknown scrapper provider")
