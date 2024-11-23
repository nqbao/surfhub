import os
from pydantic import BaseModel
from typing import Optional, List

class SerpRequestOptions(BaseModel):
    lang: Optional[str]
    country: Optional[str]
    extra_options: Optional[dict]

class SerpResult(BaseModel):
    title : str
    link : str
    snippet : str
    prefix: str


class BaseSerp:
    default_api_url : str = None
    
    def __init__(self, api_key : str = None):
        if not self.default_api_url:
            raise NotImplementedError("default_api_url is not set")
        
        self._api_key = api_key
    
    def serp(self, query : str, page = None, num = None, options : Optional[SerpRequestOptions] = None) -> List[SerpResult]:
        raise NotImplementedError()

    @property
    def endpoint(self) -> str:
        return os.environ.get("SERP_API_URL", self.default_api_url)

    @property
    def api_key(self) -> str:
        return self._api_key or os.environ.get("SERP_API_KEY")

    @property
    def timeout(self) -> int:
        return int(os.environ.get("SERP_HTTP_TIMEOUT", 10))
