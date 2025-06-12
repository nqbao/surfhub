from .model import SerpResult, SerpResponse, SerpApi
from bs4 import BeautifulSoup
from typing import List, Optional
from surfhub.utils import hash_dict
import httpx

class DuckDuckGo(SerpApi):
    """
    Search DuckDuckGo via HTML scraping (raw SerpApi interface)
    """
    api_url = "https://html.duckduckgo.com/html/"
    timeout = 30

    def __init__(self, cache=None):
        self.cache = cache

    def get_params(self, query, page=None, num=None, options=None):
        params = {
            "q": query,
            "kl": "us-en",
        }

        # does not really work
        if page is None and num is None:
            params["s"] = (page - 1) * num

        return params

    def parse(self, resp: str) -> List[SerpResult]:
        soup = BeautifulSoup(resp, "html.parser")
        results = []
        print(resp)
        for result in soup.select(".result__body"):
            title_tag = result.select_one(".result__title .result__a")
            href = title_tag["href"] if title_tag else None
            title = title_tag.get_text(strip=True) if title_tag else None
            snippet_tag = result.select_one(".result__snippet")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
            if title and href:
                results.append(
                    SerpResult(
                        title=title,
                        link=href,
                        snippet=snippet,
                        prefix=""
                    )
                )
        return results

    def serp(self, query: str, page=None, num=None, options: Optional[dict] = None) -> SerpResponse:
        params = self.get_params(query, page, num, options)
        cache_key = None
        items = None
        cached = False
        if self.cache:
            cache_key = hash_dict({**params, "endpoint": self.api_url, "provider": self.__class__.__name__})
            items = self.cache.get(cache_key)
            cached = items is not None

        if items is None:
            if params.get("s"):
                # do a post with params
                resp = httpx.post(self.api_url, data=params, timeout=self.timeout, follow_redirects=True).text
            else:
                resp = httpx.get(self.api_url, params=params, timeout=self.timeout, follow_redirects=True).text
            items = self.parse(resp)

        if self.cache and cache_key:
            self.cache.set(cache_key, items)

        return SerpResponse(items=items, cached=cached)
