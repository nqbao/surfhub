import abc
import httpx
from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict
from enum import Enum
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

    @field_validator("date_start", "date_end")
    @classmethod
    def validate_date_format(cls, v):
        if v is None:
            return v
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v


class SerpResult(BaseModel):
    title: str
    link: str
    snippet: str
    prefix: str


class SerpResponse(BaseModel):
    items: List[SerpResult]
    cached: Optional[bool]
    metadata: Optional[dict] = None


class DuckDuckGoSerpResponse(SerpResponse):
    vqd: Optional[str] = None


class SerpApi(abc.ABC):
    @abc.abstractmethod
    def serp(self, query: str, page=None, num=None, options: Optional[SerpRequestOptions] = None) -> SerpResponse:
        pass

    async def async_serp(
        self, query: str, page=None, num=None, options: Optional[SerpRequestOptions] = None
    ) -> SerpResponse:
        return self.serp(query, page, num, options)


class BaseSerper(SerpApi):
    default_api_url: str = None
    _api_key: str = None
    _api_url: str = None
    _timeout: int = 30

    def __init__(self, api_key: str = None):
        if not self.default_api_url:
            raise NotImplementedError("default_api_url is not set")

        self._api_key = api_key

    @property
    def request_method(self) -> str:
        return "GET"

    @property
    def request_headers(self) -> Dict[str, str]:
        return {}

    def build_response(self, items: List[SerpResult], cached: bool = False, resp_data=None) -> SerpResponse:
        return SerpResponse(items=items, cached=cached)

    def _fetch_and_parse(self, client: httpx.Client, params: dict):
        headers = {**self.request_headers}
        if self.request_method == "POST":
            resp = client.post(self.endpoint, json=params, headers=headers, timeout=self.timeout)
        else:
            resp = client.get(self.endpoint, params=params, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        items = self.parse_result(data)
        return items, data

    async def _async_fetch_and_parse(self, client: httpx.AsyncClient, params: dict):
        headers = {**self.request_headers}
        if self.request_method == "POST":
            resp = await client.post(self.endpoint, json=params, headers=headers, timeout=self.timeout)
        else:
            resp = await client.get(self.endpoint, params=params, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        items = self.parse_result(data)
        return items, data

    def serp(self, query: str, page=None, num=None, options: Optional[SerpRequestOptions] = None) -> SerpResponse:
        params = self.get_serp_params(query, page, num, options)
        with httpx.Client() as client:
            items, resp_data = self._fetch_and_parse(client, params)
        return self.build_response(items, False, resp_data)

    async def async_serp(
        self, query: str, page=None, num=None, options: Optional[SerpRequestOptions] = None
    ) -> SerpResponse:
        params = self.get_serp_params(query, page, num, options)
        async with httpx.AsyncClient() as client:
            items, resp_data = await self._async_fetch_and_parse(client, params)
        return self.build_response(items, False, resp_data)

    @abc.abstractmethod
    def get_serp_params(self, query: str, page=None, num=None, options: Optional[SerpRequestOptions] = None) -> dict:
        pass

    @abc.abstractmethod
    def parse_result(self, resp) -> List[SerpResult]:
        pass

    @property
    def endpoint(self) -> str:
        return self._api_url or self.default_api_url

    @endpoint.setter
    def endpoint(self, value: str):
        self._api_url = value

    @property
    def api_key(self) -> str:
        return self._api_key

    @api_key.setter
    def api_key(self, value: str):
        self._api_key = value

    @property
    def timeout(self) -> int:
        return self._timeout

    @timeout.setter
    def timeout(self, value: int):
        self._timeout = value
