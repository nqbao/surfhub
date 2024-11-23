from .model import BaseScrapper, ScrapperOptions
import os
import httpx

class LocalScrapper(BaseScrapper):
    """
    A scrapper that runs on local
    """
    def scrape(self, url: str, options : ScrapperOptions = None) -> bytes:
        proxies = None
        if self.http_proxy or self.https_proxy:
            proxies = {
                "http": self.http_proxy,
                "https": self.https_proxy
            }
        
        return httpx.get(
            url,
            timeout=self.timeout,
            proxies=proxies,
            verify=self.verify_ca
        ).content

    @property
    def http_proxy(self) -> str:
        return os.environ.get("SCRAPPER_HTTP_PROXY", "")

    @property
    def https_proxy(self) -> str:
        return os.environ.get("SCRAPPER_HTTPS_PROXY", "")
    
    @property
    def verify_ca(self) -> int:
        return os.environ.get("SCRAPPER_VERIFY_CA", "1") in ["1", "true", "yes"]

    @property
    def endpoint(self) -> str:
        return os.environ.get("SCRAPPER_API_URL", self.default_api_url)
