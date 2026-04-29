from typing import List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote
import httpx

from .model import BaseSerper, SerpResult, SerpRequestOptions, DuckDuckGoSerpResponse
from surfhub.errors import SerpApiError


class DuckDuckGo(BaseSerper):
    """Search DuckDuckGo via HTML scraping with pagination support."""

    default_api_url = "https://html.duckduckgo.com/html/"

    @property
    def request_method(self) -> str:
        return "POST"

    @property
    def request_headers(self) -> dict:
        return {
            "User-agent": "Surfhub-Agent/0.0.1",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Site": "same-origin",
            "Referer": "https://html.duckduckgo.com/",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def serp(self, query: str, page=None, num=None, vqd: Optional[str] = None, options: Optional[SerpRequestOptions] = None) -> DuckDuckGoSerpResponse:
        if vqd:
            extra = dict(options.extra_options or {}) if options else {}
            extra["vqd"] = vqd
            if options:
                options = options.model_copy(update={"extra_options": extra})
            else:
                options = SerpRequestOptions(extra_options=extra)
        return super().serp(query, page, num, options)

    async def async_serp(self, query: str, page=None, num=None, vqd: Optional[str] = None, options: Optional[SerpRequestOptions] = None) -> DuckDuckGoSerpResponse:
        if vqd:
            extra = dict(options.extra_options or {}) if options else {}
            extra["vqd"] = vqd
            if options:
                options = options.model_copy(update={"extra_options": extra})
            else:
                options = SerpRequestOptions(extra_options=extra)
        return await super().async_serp(query, page, num, options)

    def get_serp_params(self, query: str, page=None, num=None, options: Optional[SerpRequestOptions] = None) -> dict:
        params = {
            "q": query,
            "b": "",
            "kl": "us-en",
        }

        if options:
            if options.lang:
                params["kl"] = options.lang
            if options.time_range:
                params["df"] = options.time_range.value

        if page is not None and page > 1:
            extra_options = options.extra_options if options else {}
            vqd = extra_options.get("vqd")
            if not vqd:
                raise SerpApiError("vqd is required for page > 1. Call page 1 first to obtain it.")

            offset = 10 + (page - 2) * 15
            params["s"] = str(offset)
            params["dc"] = str(offset + 1)
            params["nextParams"] = ""
            params["api"] = "d.js"
            params["o"] = "json"
            params["v"] = "l"
            params["vqd"] = vqd

        return params

    def _fetch_and_parse(self, client: httpx.Client, params: dict, cache_key: str):
        headers = {**self.request_headers}
        cookies = {}
        if "kl" in params:
            cookies["kl"] = params["kl"]
        if "df" in params:
            cookies["df"] = params["df"]
        resp = client.post(self.endpoint, data=params, headers=headers, cookies=cookies, timeout=self.timeout, follow_redirects=True)
        resp.raise_for_status()
        items = self.parse_result(resp.text)
        if self.cache and cache_key:
            self.cache.set(cache_key, items)
        return items, resp.text

    async def _async_fetch_and_parse(self, client: httpx.AsyncClient, params: dict, cache_key: str):
        headers = {**self.request_headers}
        cookies = {}
        if "kl" in params:
            cookies["kl"] = params["kl"]
        if "df" in params:
            cookies["df"] = params["df"]
        resp = await client.post(self.endpoint, data=params, headers=headers, cookies=cookies, timeout=self.timeout, follow_redirects=True)
        resp.raise_for_status()
        items = self.parse_result(resp.text)
        if self.cache and cache_key:
            self.cache.set(cache_key, items)
        return items, resp.text

    def parse_result(self, resp: str) -> List[SerpResult]:
        soup = BeautifulSoup(resp, "html.parser")
        results = []
        for result in soup.select(".result__body"):
            title_tag = result.select_one(".result__title .result__a")
            href = title_tag["href"] if title_tag else None
            title = title_tag.get_text(strip=True) if title_tag else None
            snippet_tag = result.select_one(".result__snippet")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
            if title and href:
                if "uddg=" in href:
                    parsed_url = urlparse(href)
                    params_parsed = parse_qs(parsed_url.query)
                    href = unquote(params_parsed["uddg"][0])
                elif "y.js" in href:
                    continue

                results.append(
                    SerpResult(
                        title=title,
                        link=href,
                        snippet=snippet,
                        prefix=""
                    )
                )
        return results

    def build_response(self, items: List[SerpResult], cached: bool, resp_data=None) -> DuckDuckGoSerpResponse:
        vqd = None
        if resp_data:
            soup = BeautifulSoup(resp_data, "html.parser")
            vqd_input = soup.find("input", {"name": "vqd"})
            if vqd_input:
                vqd = vqd_input.get("value")
        return DuckDuckGoSerpResponse(items=items, cached=cached, vqd=vqd)
