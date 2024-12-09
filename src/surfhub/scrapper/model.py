from pydantic import BaseModel
import os

class ScrapperOptions(BaseModel):
    pass

class BaseScrapper:
    default_api_url = ""
    
    def __init__(self, api_key: str = None):
        self._api_key = api_key
    
    def scrape(self, url: str, options : ScrapperOptions = None) -> bytes:
        """
        Scrapes the content of a given URL and returns it content
        """
        raise NotImplementedError("This method must be implemented by the subclass")

    async def async_scrape(self, url: str, options : ScrapperOptions = None) -> str:
        """
        Scrapes the content of a given URL asynchronously and returns it content
        """
        return self.scrape(url, options)

    @property
    def timeout(self) -> int:
        """
        Timeout in seconds for the HTTP request
        """
        return int(os.environ.get("SCRAPPER_HTTP_TIMEOUT", 30))

    @property
    def api_key(self) -> str:
        return self._api_key or os.environ.get("SCRAPPER_API_KEY", "")

    @property
    def endpoint(self) -> str:
        return os.environ.get("SCAPPER_API_URL", self.default_api_url)
