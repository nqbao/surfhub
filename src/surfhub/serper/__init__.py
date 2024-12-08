import os
from .model import BaseSerp, SerpResult, SerpRequestOptions
from .valueserp import ValueSerp
from .google import GoogleCustomSearch
from .serper import SerperDev
from surfhub.cache import get_cache


def get_serp(provider=None, cache=None, **kwargs) -> BaseSerp:
    provider = provider or os.environ.get("SERP_PROVIDER")
    if not provider:
        raise ValueError("Please provide a SERP provider")
     
    if not cache and os.environ.get("SERP_CACHE_TTL"):
        cache = get_cache(default_ttl=int(os.environ.get("SERP_CACHE_TTL")))
     
    if provider == "valueserp":
        return ValueSerp(cache=cache, **kwargs)
    
    if provider == "google":
        return GoogleCustomSearch(cache=cache, **kwargs)
    
    if provider == "serper":
        return SerperDev(cache=cache, **kwargs)
    
    raise ValueError(f"Unknown provider: {provider}")
