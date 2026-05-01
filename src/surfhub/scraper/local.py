from .model import Scraper, ScraperOptions, ScraperResponse
import httpx

class LocalScraper(Scraper):
    _http_proxy : str = ""
    _https_proxy : str = ""
    _verify_ca : bool = True
    
    """
    A scraper that runs on local
    """
    def _get_proxy(self) -> str | None:
        return self.http_proxy or self.https_proxy or None

    def scrape(self, url: str, options : ScraperOptions = None) -> ScraperResponse:
        proxy = self._get_proxy()

        with httpx.Client(proxy=proxy, verify=self.verify_ca) as client:
            resp = client.get(url, timeout=self.timeout)
        
        return ScraperResponse(
            content=resp.content,
            content_type=resp.headers.get("content-type", ""),
            encoding=resp.encoding or "utf-8",
            status_code=resp.status_code,
            final_url=str(resp.url),
        )

    async def async_scrape(self, url: str, options : ScraperOptions = None) -> ScraperResponse:
        proxy = self._get_proxy()

        async with httpx.AsyncClient(proxy=proxy, verify=self.verify_ca) as client:
            resp = await client.get(url, timeout=self.timeout)
        
        return ScraperResponse(
            content=resp.content,
            content_type=resp.headers.get("content-type", ""),
            encoding=resp.encoding or "utf-8",
            status_code=resp.status_code,
            final_url=str(resp.url),
        )

    @property
    def http_proxy(self) -> str:
        return self._http_proxy
    
    @http_proxy.setter
    def http_proxy(self, value: str):
        self._http_proxy = value

    @property
    def https_proxy(self) -> str:
        return self._https_proxy
    
    @https_proxy.setter
    def https_proxy(self, value: str):
        self._https_proxy = value
    
    @property
    def verify_ca(self) -> bool:
        return self._verify_ca
    
    @verify_ca.setter
    def verify_ca(self, value: bool):
        self._verify_ca = value
