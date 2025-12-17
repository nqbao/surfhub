import abc
import httpx
from pydantic import BaseModel, field_validator
from typing import Optional, List
from enum import Enum
from surfhub.cache import Cache
from surfhub.utils import hash_dict
import re


class TimeRange(str, Enum):
    """Time range filter for search results"""
    DAY = "d"
    WEEK = "w"
    MONTH = "m"
    YEAR = "y"

class SerpRequestOptions(BaseModel):
    """
    Options for configuring SERP (Search Engine Results Page) requests.

    Attributes:
        lang (Optional[str]): Language code for search results (e.g., 'en', 'es', 'fr').
        country (Optional[str]): Country code for geographically targeted results (e.g., 'us', 'uk', 'ca').
        location (Optional[str]): Specific location name for localized search results.
        google_domain (Optional[str]): Google domain to use for the search (e.g., 'google.com', 'google.co.uk').
        time_range (Optional[TimeRange]): Time filter - DAY, WEEK, MONTH, or YEAR.
        date_start (Optional[str]): Start date for custom date range in YYYY-MM-DD format.
        date_end (Optional[str]): End date for custom date range in YYYY-MM-DD format.
        extra_options (Optional[dict]): Additional custom options to pass to the SERP API.
    """
    lang: Optional[str] = None
    country: Optional[str] = None
    location: Optional[str] = None
    google_domain: Optional[str] = None
    time_range: Optional[TimeRange] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    extra_options: Optional[dict] = None
    
    @field_validator('date_start', 'date_end')
    @classmethod
    def validate_date_format(cls, v):
        if v is None:
            return v
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError('Date must be in YYYY-MM-DD format')
        return v

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


class BaseSerper(SerpApi):
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
