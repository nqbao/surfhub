from .model import BaseSerper, SerpResult, SerpRequestOptions
from .valueserp import ValueSerp
from .google import GoogleCustomSearch
from .serper import SerperDev
from surfhub.cache.base import Cache


def get_serper(provider, cache: Cache=None, **kwargs) -> BaseSerper:
    if not provider:
        raise ValueError("Please provide a SERP provider")
     
    if provider == "valueserp":
        return ValueSerp(cache=cache, **kwargs)
    
    if provider == "google":
        return GoogleCustomSearch(cache=cache, **kwargs)
    
    if provider == "serper":
        return SerperDev(cache=cache, **kwargs)
    
    raise ValueError(f"Unknown provider: {provider}")
