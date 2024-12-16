from .model import Scrapper, ScrapperOptions, ScrapperResponse
import os
import httpx

class LocalScrapper(Scrapper):
    """
    A scrapper that runs on local
    """
    def scrape(self, url: str, options : ScrapperOptions = None) -> ScrapperResponse:
        proxies = None
        if self.http_proxy or self.https_proxy:
            proxies = {
                "http://": self.http_proxy,
                "https://": self.https_proxy
            }

        resp = httpx.get(
            url,
            timeout=self.timeout,
            proxies=proxies,
            verify=self.verify_ca
        )
        
        return ScrapperResponse(
            content=resp.content,
            status_code=resp.status_code,
            final_url=resp.url,
        )

    async def async_scrape(self, url: str, options : ScrapperOptions = None) -> ScrapperResponse:
        return self.scrape(url, options)

    @property
    def http_proxy(self) -> str:
        return os.environ.get("SCRAPPER_HTTP_PROXY", "")

    @property
    def https_proxy(self) -> str:
        return os.environ.get("SCRAPPER_HTTPS_PROXY", "")
    
    @property
    def verify_ca(self) -> int:
        return os.environ.get("SCRAPPER_PROXY_VERIFY", "1") in ["1", "true", "yes"]
