import abc
import os
import httpx
from pydantic import BaseModel

class ScrapperOptions(BaseModel):
    pass

class ScrapperResponse(BaseModel):
    content: bytes
    final_url: str
    status_code: int
    
    def text(self, encoding: str = "utf-8") -> str:
        return self.content.decode(encoding)

class Scrapper(abc.ABC):
    _timeout = None
    
    @abc.abstractmethod
    def scrape(self, url: str, options: ScrapperOptions = None) -> ScrapperResponse:
        pass
    
    @abc.abstractmethod
    async def async_scrape(self, url: str, options: ScrapperOptions = None) -> ScrapperResponse:
        pass
    
    @property
    def timeout(self) -> int:
        """
        Timeout in seconds for the HTTP request
        """
        
        if self._timeout is not None:
            return self._timeout

        return int(os.environ.get("SCRAPPER_HTTP_TIMEOUT", 30))
    
    @timeout.setter
    def timeout(self, value: int):
        self._timeout = value


class BaseScrapper(Scrapper):
    default_api_url = ""
    
    def __init__(self, api_key: str = None):
        self._api_key = api_key

    def scrape(self, url, options : ScrapperOptions = None) -> ScrapperResponse:
        with httpx.Client(
            timeout=self.timeout
        ) as client:
            resp = client.send(
                self.prepare_request(url, options),
                auth=self.get_request_auth(),
            )
            
        self.validate_response(resp)

        return self.parse_response(url, resp)

    async def async_scrape(self, url: str, options : ScrapperOptions = None) -> ScrapperResponse:
        """
        Scrapes the content of a given URL asynchronously and returns it content
        """
        async with httpx.AsyncClient(
            timeout=self.timeout
        ) as client:
            resp = await client.send(
                self.prepare_request(url, options),
                auth=self.get_request_auth(),
            )
            
        self.validate_response(resp)
        return self.parse_response(url, resp)

    @abc.abstractmethod
    def prepare_request(self, url: str, options : ScrapperOptions = None) -> httpx.Request:
        pass
    
    @abc.abstractmethod
    def parse_response(self, url: str, resp: httpx.Response) -> ScrapperResponse:
        pass

    def get_request_auth(self):
        return None

    def validate_response(self, resp: httpx.Response):
        if resp.status_code != 200:
            raise Exception("Unexpected status code: " + str(resp.status_code))

    @property
    def api_key(self) -> str:
        return self._api_key or os.environ.get("SCRAPPER_API_KEY", "")

    @property
    def endpoint(self) -> str:
        return os.environ.get("SCAPPER_API_URL", self.default_api_url)
