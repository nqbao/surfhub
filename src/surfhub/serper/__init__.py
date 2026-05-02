from .model import BaseSerper, SerpResult, SerpRequestOptions, TimeRange
from .valueserp import ValueSerp
from .google import GoogleCustomSearch
from .serper import SerperDev
from .duckduckgo import DuckDuckGo
from .tavily import Tavily
from .serpapi import SerpApi
from .you import YouSearch
from .brave import BraveSearch
from .exa import ExaSearch
from .perplexity import PerplexitySearch
from .jina import JinaSearch
from .cached import CachedSerper
from surfhub.cache.base import Cache


def get_serper(provider, cache: Cache = None, api_key=None, **kwargs) -> BaseSerper:
    if not provider:
        raise ValueError("Please provide a SERP provider")

    kwargs["api_key"] = api_key

    if provider == "valueserp":
        serper = ValueSerp(**kwargs)
    elif provider == "google":
        serper = GoogleCustomSearch(**kwargs)
    elif provider == "serper":
        serper = SerperDev(**kwargs)
    elif provider == "serpapi":
        serper = SerpApi(**kwargs)
    elif provider == "duckduckgo":
        serper = DuckDuckGo(**kwargs)
    elif provider == "tavily":
        serper = Tavily(**kwargs)
    elif provider == "you":
        serper = YouSearch(**kwargs)
    elif provider == "brave":
        serper = BraveSearch(**kwargs)
    elif provider == "exa":
        serper = ExaSearch(**kwargs)
    elif provider == "perplexity":
        serper = PerplexitySearch(**kwargs)
    elif provider == "jina":
        serper = JinaSearch(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}")

    if cache:
        return CachedSerper(serper, cache)
    return serper
