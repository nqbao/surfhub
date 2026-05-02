from typing import List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote
import httpx

from .model import BaseSerper, SerpResult, SerpRequestOptions, DuckDuckGoSerpResponse
from surfhub.errors import SerpApiError, RateLimitError


class DuckDuckGo(BaseSerper):
    """Search DuckDuckGo via HTML scraping with pagination support."""

    default_api_url = "https://html.duckduckgo.com/html/"

    def __init__(self, api_key: str = None):
        super().__init__(api_key=api_key)
        self._client = None
        self._async_client = None

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout)
        return self._client

    def _get_async_client(self) -> httpx.AsyncClient:
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(timeout=self.timeout)
        return self._async_client

    def close(self):
        if self._client:
            self._client.close()
            self._client = None
        if self._async_client:
            self._async_client.close()
            self._async_client = None

    @property
    def request_method(self) -> str:
        return "GET"

    @property
    def request_headers(self) -> dict:
        return {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def serp(
        self, query: str, page=None, num=None, vqd: Optional[str] = None, options: Optional[SerpRequestOptions] = None
    ) -> DuckDuckGoSerpResponse:
        if vqd:
            extra = dict(options.extra_options or {}) if options else {}
            extra["vqd"] = vqd
            if options:
                options = options.model_copy(update={"extra_options": extra})
            else:
                options = SerpRequestOptions(extra_options=extra)

        params = self.get_serp_params(query, page, num, options)
        client = self._get_client()
        items, resp_text = self._fetch_and_parse(client, params)
        return self.build_response(items, resp_text)

    async def async_serp(
        self, query: str, page=None, num=None, vqd: Optional[str] = None, options: Optional[SerpRequestOptions] = None
    ) -> DuckDuckGoSerpResponse:
        if vqd:
            extra = dict(options.extra_options or {}) if options else {}
            extra["vqd"] = vqd
            if options:
                options = options.model_copy(update={"extra_options": extra})
            else:
                options = SerpRequestOptions(extra_options=extra)

        params = self.get_serp_params(query, page, num, options)
        client = self._get_async_client()
        items, resp_text = await self._async_fetch_and_parse(client, params)
        return self.build_response(items, resp_text)

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

    def _fetch_and_parse(self, client: httpx.Client, params: dict):
        headers = {**self.request_headers}
        cookies = {}
        if "kl" in params:
            cookies["kl"] = params["kl"]
        if "df" in params:
            cookies["df"] = params["df"]
        resp = client.get(
            self.endpoint, params=params, headers=headers, cookies=cookies, timeout=self.timeout, follow_redirects=True
        )
        resp.raise_for_status()
        self._check_throttle(resp)
        items = self.parse_result(resp.text)
        return items, resp.text

    async def _async_fetch_and_parse(self, client: httpx.AsyncClient, params: dict):
        headers = {**self.request_headers}
        cookies = {}
        if "kl" in params:
            cookies["kl"] = params["kl"]
        if "df" in params:
            cookies["df"] = params["df"]
        resp = await client.get(
            self.endpoint, params=params, headers=headers, cookies=cookies, timeout=self.timeout, follow_redirects=True
        )
        resp.raise_for_status()
        self._check_throttle(resp)
        items = self.parse_result(resp.text)
        return items, resp.text

    def _check_throttle(self, resp: httpx.Response):
        if resp.status_code == 202 or "result__body" not in resp.text:
            raise RateLimitError(
                "DuckDuckGo returned a non-results page — likely rate-limited or blocked. Try again later."
            )

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

                results.append(SerpResult(title=title, link=href, snippet=snippet, prefix=""))
        return results

    def build_response(self, items: List[SerpResult], resp_data=None) -> DuckDuckGoSerpResponse:
        vqd = None
        if resp_data:
            soup = BeautifulSoup(resp_data, "html.parser")
            vqd_input = soup.find("input", {"name": "vqd"})
            if vqd_input:
                vqd = vqd_input.get("value")
        return DuckDuckGoSerpResponse(items=items, cached=False, vqd=vqd)
