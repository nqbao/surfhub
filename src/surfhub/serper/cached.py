from typing import Optional
from surfhub.cache import Cache
from surfhub.utils import hash_dict
from .model import SerpApi, SerpResponse, SerpRequestOptions


class CachedSerper(SerpApi):
    def __init__(self, inner: SerpApi, cache: Cache):
        self._inner = inner
        self._cache = cache

    @property
    def inner(self) -> SerpApi:
        return self._inner

    def _cache_key(self, query: str, page, num, options: Optional[SerpRequestOptions] = None, **kwargs) -> str:
        params = {"query": query, "page": page, "num": num}
        if options:
            params["options"] = options.model_dump()
        params["provider"] = self._inner.__class__.__name__
        if kwargs:
            params["extra"] = kwargs
        return hash_dict(params)

    def serp(
        self, query: str, page=None, num=None, options: Optional[SerpRequestOptions] = None, **kwargs
    ) -> SerpResponse:
        key = self._cache_key(query, page, num, options, **kwargs)
        cached = self._cache.get(key)
        if cached is not None:
            return cached.model_copy(update={"cached": True})
        result = self._inner.serp(query, page=page, num=num, options=options, **kwargs)
        result.cached = False
        self._cache.set(key, result)
        return result

    async def async_serp(
        self, query: str, page=None, num=None, options: Optional[SerpRequestOptions] = None, **kwargs
    ) -> SerpResponse:
        key = self._cache_key(query, page, num, options, **kwargs)
        cached = self._cache.get(key)
        if cached is not None:
            return cached.model_copy(update={"cached": True})
        result = await self._inner.async_serp(query, page=page, num=num, options=options, **kwargs)
        result.cached = False
        self._cache.set(key, result)
        return result
