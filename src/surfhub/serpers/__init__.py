import os
from .model import *
from .valueserp import *
from .google import *
from surfhub.cache import get_cache


def get_serp(provider=None, cache=None):
    provider = provider or os.environ.get("SERP_PROVIDER")
    if not provider:
        raise ValueError("Please provide a SERP provider")
     
    if not cache and os.environ.get("SERP_CACHE_TTL"):
        cache = get_cache(default_ttl=int(os.environ.get("SERP_CACHE_TTL")))
     
    if provider == "valueserp":
        return ValueSerp(cache=cache)
    
    if provider == "google":
        return GoogleSerp(cache=cache)
    
    raise ValueError(f"Unknown provider: {provider}")
