import abc
import httpx
from pydantic import BaseModel

class ScraperOptions(BaseModel):
    pass

class ScraperResponse(BaseModel):
    content: bytes
    final_url: str
    status_code: int
    
    def text(self, encoding: str = "utf-8") -> str:
        return self.content.decode(encoding)

class Scraper(abc.ABC):
    _timeout : int = 30
    
    @abc.abstractmethod
    def scrape(self, url: str, options: ScraperOptions = None) -> ScraperResponse:
        pass
    
    @abc.abstractmethod
    async def async_scrape(self, url: str, options: ScraperOptions = None) -> ScraperResponse:
        pass
    
    @property
    def timeout(self) -> int:
        """
        Timeout in seconds for the HTTP request
        """
        return self._timeout
    
    @timeout.setter
    def timeout(self, value: int):
        self._timeout = value

class BaseScraper(Scraper):
    default_api_url = ""
    _api_key : str = None
    _api_url : str = None
    _retries : int = 3
    
    def __init__(self, api_key: str = None):
        self._api_key = api_key

    def scrape(self, url, options : ScraperOptions = None) -> ScraperResponse:
        with httpx.Client(
            timeout=self.timeout
        ) as client:
            for i in range(self.retries):
                resp = None
                try:
                    resp = client.send(
                        self.prepare_request(url, options),
                        auth=self.get_request_auth(),
                    )
                    
                    self.validate_response(resp)
                except Exception as e:
                    if i < self.retries - 1 and self.is_retriable_error(e, resp):
                        continue
                    
                    raise e

                break

        return self.parse_response(url, resp)

    async def async_scrape(self, url: str, options : ScraperOptions = None) -> ScraperResponse:
        """
        Scrapes the content of a given URL asynchronously and returns it content
        """
        async with httpx.AsyncClient(
            timeout=self.timeout
        ) as client:
            for i in range(self.retries):
                resp = None
                try:
                    resp = await client.send(
                        self.prepare_request(url, options),
                        auth=self.get_request_auth(),
                    )
                    
                    self.validate_response(resp)
                except Exception as e:
                    if i < self.retries - 1 and self.is_retriable_error(e, resp):
                        continue

                    raise e

        return self.parse_response(url, resp)

    @abc.abstractmethod
    def prepare_request(self, url: str, options : ScraperOptions = None) -> httpx.Request:
        pass
    
    @abc.abstractmethod
    def parse_response(self, url: str, resp: httpx.Response) -> ScraperResponse:
        pass

    def get_request_auth(self):
        return None

    def validate_response(self, resp: httpx.Response):
        if resp.status_code != 200:
            raise Exception("Unexpected status code: " + str(resp.status_code))

    def is_retriable_error(self, ex: Exception, resp: httpx.Response):
        # allow retries for connection errors
        if isinstance(ex, httpx.TransportError):
            return True

        return resp and resp.status_code >= 500

    @property
    def api_key(self) -> str:
        return self._api_key
    
    @api_key.setter
    def api_key(self, value: str):
        self._api_key = value

    @property
    def api_url(self) -> str:
        return self._api_url or self.default_api_url
    
    @api_url.setter
    def api_url(self, value: str):
        self._api_url = value

    @property
    def retries(self) -> int:
        return self._retries
    
    @retries.setter
    def retries(self, value: int):
        self._retries = value
