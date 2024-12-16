from .model import Scrapper, ScrapperOptions, ScrapperResponse
import httpx

class LocalScrapper(Scrapper):
    _http_proxy : str = ""
    _https_proxy : str = ""
    _verify_ca : bool = True
    
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
    def verify_ca(self) -> int:
        return self._verify_ca
    
    @verify_ca.setter
    def verify_ca(self, value: int):
        self._verify_ca = value
