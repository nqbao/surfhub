from .model import BaseSerper, SerpResult, SerpRequestOptions
from .valueserp import ValueSerp
from .google import GoogleCustomSearch
from .serper import SerperDev
from .duckduckgo import DuckDuckGo
from .tavily import Tavily
from surfhub.cache.base import Cache


def get_serper(provider, cache: Cache=None, api_key=None, **kwargs) -> BaseSerper:
    if not provider:
        raise ValueError("Please provide a SERP provider")
    
    kwargs["api_key"] = api_key
     
    if provider == "valueserp":
        return ValueSerp(cache=cache, **kwargs)
    
    if provider == "google":
        return GoogleCustomSearch(cache=cache, **kwargs)
    
    if provider == "serper":
        return SerperDev(cache=cache, **kwargs)
    
    if provider == "duckduckgo":
        return DuckDuckGo(cache=cache, **kwargs)
    
    if provider == "tavily":
        return Tavily(cache=cache, **kwargs)
    
    raise ValueError(f"Unknown provider: {provider}")
