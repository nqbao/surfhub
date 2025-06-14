from typing import List
from surfhub.serper.model import SerpResult, BaseSerper, SerpResponse
import httpx

class Tavily(BaseSerper):
    """
    Search via Tavily API
    """
    default_api_url = "https://api.tavily.com/search"

    def get_serp_params(self, query, page=None, num=None, options=None):
        params = {
            "query": query,
        }
        if num is not None:
            params["max_results"] = num
        if options and options.extra_options:
            params.update(options.extra_options)
        return params

    def serp(self, query: str, page=None, num=None, options=None):
        params = self.get_serp_params(query, page, num, options)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        resp = httpx.post(self.endpoint, json=params, headers=headers, timeout=self.timeout)
        items = self.parse_result(resp.json())
        return SerpResponse(items=items, cached=False)

    async def async_serp(self, query: str, page=None, num=None, options=None):
        params = self.get_serp_params(query, page, num, options)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(self.endpoint, json=params, headers=headers)
            items = self.parse_result(resp.json())
        return SerpResponse(items=items, cached=False)

    def parse_result(self, resp) -> List[SerpResult]:
        results = resp.get("results", [])
        return [
            SerpResult(
                title=i.get("title"),
                link=i.get("url"),
                snippet=i.get("content", ""),
                prefix=""
            )
            for i in results
        ]
