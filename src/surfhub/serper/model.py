import abc
import httpx
from pydantic import BaseModel
from typing import Optional, List
from surfhub.cache import Cache
from surfhub.utils import hash_dict

class SerpRequestOptions(BaseModel):
    lang: Optional[str]
    country: Optional[str]
    location: Optional[str]
    google_domain: Optional[str]
    extra_options: Optional[dict]

class SerpResult(BaseModel):
    title : str
    link : str
    snippet : str
    prefix: str

class SerpResponse(BaseModel):
    items: List[SerpResult]
    cached : Optional[bool]

class SerpApi(abc.ABC):
    @abc.abstractmethod
    def serp(self, query : str, page = None, num = None, options : Optional[SerpRequestOptions] = None) -> SerpResponse:
        pass

    async def async_serp(self, query : str, page = None, num = None, options : Optional[SerpRequestOptions] = None) -> SerpResponse:
        return self.serp(query, page, num, options)


class BaseSerp(SerpApi):
    default_api_url : str = None
    cache : Optional[Cache] = None
    _api_key : str = None
    _api_url : str = None
    _timeout : int = 30

    def __init__(self, api_key : str = None, cache : Optional[Cache] = None):
        if not self.default_api_url:
            raise NotImplementedError("default_api_url is not set")
        
        self._api_key = api_key
        self.cache = cache
    
    def serp(self, query : str, page = None, num = None, options : Optional[SerpRequestOptions] = None) -> SerpResponse:
        params = self.get_serp_params(query, page, num, options)
        
        cache_key = None
        items  = None
        cached = False
        if self.cache:
            cache_key = hash_dict({**params, "endpoint": self.endpoint, "provider": self.__class__.__name__})
            items = self.cache.get(cache_key)
            cached = items is not None
        
        if items is None:
            resp = httpx.get(self.endpoint, params=params, timeout=self.timeout).json()
            items = self.parse_result(resp)
        
        if self.cache and cache_key:
            self.cache.set(cache_key, items)
        
        return SerpResponse(items=items, cached=cached)

    async def async_serp(self, query : str, page = None, num = None, options : Optional[SerpRequestOptions] = None) -> SerpResponse:
        params = self.get_serp_params(query, page, num, options)
        
        cache_key = None
        items = None
        cached = False
        if self.cache:
            cache_key = hash_dict({**params, "endpoint": self.endpoint, "provider": self.__class__.__name__})
            items = self.cache.get(cache_key)
            cached = items is not None
        
        if items is None:
            async with httpx.AsyncClient() as client:
                resp = await client.get(self.endpoint, params=params, timeout=self.timeout)
                resp = resp.json()
                items = self.parse_result(resp)
        
        if self.cache and cache_key:
            self.cache.set(cache_key, items)
        
        return SerpResponse(items=items, cached=cached)

    @abc.abstractmethod
    def get_serp_params(self, query : str, page = None, num = None, options : Optional[SerpRequestOptions] = None) -> dict:
        pass

    @abc.abstractmethod
    def parse_result(self, resp) -> List[SerpResult]:
        pass

    @property
    def endpoint(self) -> str:
        return self._api_url or self.default_api_url
    
    @endpoint.setter
    def endpoint(self, value : str):
        self._api_url = value

    @property
    def api_key(self) -> str:
        return self._api_key
    
    @api_key.setter
    def api_key(self, value : str):
        self._api_key = value

    @property
    def timeout(self) -> int:
        return self._timeout
    
    @timeout.setter
    def timeout(self, value : int):
        self._timeout = value
