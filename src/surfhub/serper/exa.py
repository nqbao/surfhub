from typing import List, Optional
from surfhub.serper.model import SerpResult, BaseSerper, SerpResponse
import httpx


class ExaSearch(BaseSerper):
    """
    Search via Exa API (https://exa.ai)
    Uses neural/keyword/auto search and returns structured results.
    Auth: x-api-key header.
    """
    default_api_url = "https://api.exa.ai/search"

    def get_serp_params(self, query, page=None, num=None, options=None):
        params = {
            "query": query,
            "type": "auto",
        }

        if num is not None:
            params["numResults"] = num

        if options:
            if options.date_start:
                params["startPublishedDate"] = options.date_start + "T00:00:00.000Z"
            if options.date_end:
                params["endPublishedDate"] = options.date_end + "T23:59:59.999Z"
            if options.extra_options:
                params.update(options.extra_options)

        return params

    def _headers(self):
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def serp(self, query: str, page=None, num=None, options=None):
        params = self.get_serp_params(query, page, num, options)
        resp = httpx.post(self.endpoint, json=params, headers=self._headers(), timeout=self.timeout)
        resp.raise_for_status()
        items = self.parse_result(resp.json())
        return SerpResponse(items=items, cached=False)

    async def async_serp(self, query: str, page=None, num=None, options=None):
        params = self.get_serp_params(query, page, num, options)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(self.endpoint, json=params, headers=self._headers())
            resp.raise_for_status()
            items = self.parse_result(resp.json())
        return SerpResponse(items=items, cached=False)

    def parse_result(self, resp) -> List[SerpResult]:
        results = resp.get("results", [])
        return [
            SerpResult(
                title=r.get("title", ""),
                link=r.get("url", ""),
                snippet=r.get("text") or r.get("summary", ""),
                prefix=""
            )
            for r in results
        ]
