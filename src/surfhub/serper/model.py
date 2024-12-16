import abc
import os
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
    
class SerpApi(abc.ABC):
    @abc.abstractmethod
    def serp(self, query : str, page = None, num = None, options : Optional[SerpRequestOptions] = None) -> SerpResponse:
        pass

    async def async_serp(self, query : str, page = None, num = None, options : Optional[SerpRequestOptions] = None) -> SerpResponse:
        return self.serp(query, page, num, options)


class BaseSerp(SerpApi):
    default_api_url : str = None
    cache : Optional[Cache] = None
    
    def __init__(self, api_key : str = None, cache : Optional[Cache] = None):
        if not self.default_api_url:
            raise NotImplementedError("default_api_url is not set")
        
        self._api_key = api_key
        self.cache = cache
    
    def serp(self, query : str, page = None, num = None, options : Optional[SerpRequestOptions] = None) -> SerpResponse:
        params = self.get_serp_params(query, page, num, options)
        
        cache_key = None
        resp = None
        if self.cache:
            cache_key = hash_dict({**params, "endpoint": self.endpoint, "provider": self.__class__.__name__})
            resp = self.cache.get(cache_key)
        
        if resp is None:
            resp = httpx.get(self.endpoint, params=params, timeout=self.timeout).json()
        
        if self.cache and cache_key:
            self.cache.set(cache_key, resp)
        
        items = self.parse_result(resp)
        return SerpResponse(items=items)

    async def async_serp(self, query : str, page = None, num = None, options : Optional[SerpRequestOptions] = None) -> SerpResponse:
        params = self.get_serp_params(query, page, num, options)
        
        cache_key = None
        resp = None
        if self.cache:
            cache_key = hash_dict({**params, "endpoint": self.endpoint, "provider": self.__class__.__name__})
            resp = self.cache.get(cache_key)
        
        if resp is None:
            async with httpx.AsyncClient() as client:
                resp = await client.get(self.endpoint, params=params, timeout=self.timeout)
                resp = resp.json()
        
        if self.cache and cache_key:
            self.cache.set(cache_key, resp)
        
        items = self.parse_result(resp)
        return SerpResponse(items=items)

    @abc.abstractmethod
    def get_serp_params(self, query : str, page = None, num = None, options : Optional[SerpRequestOptions] = None) -> dict:
        pass

    @abc.abstractmethod
    def parse_result(self, resp) -> List[SerpResult]:
        pass

    @property
    def endpoint(self) -> str:
        return os.environ.get("SERP_API_URL", self.default_api_url)

    @property
    def api_key(self) -> str:
        return self._api_key or os.environ.get("SERP_API_KEY")

    @property
    def timeout(self) -> int:
        return int(os.environ.get("SERP_HTTP_TIMEOUT", 30))
