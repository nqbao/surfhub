from typing import List
from surfhub.serper.model import SerpResult, BaseSerper, SerpResponse
import httpx


class YouSearch(BaseSerper):
    """
    Search via You.com API
    https://docs.you.com/api-reference/search/v1-search.md
    """
    default_api_url = "https://ydc-index.io/v1/search"

    def get_serp_params(self, query, page=None, num=None, options=None):
        params = {
            "query": query,
        }
        
        if num is not None:
            params["count"] = num
        
        if page is not None:
            params["offset"] = page
        
        if options:
            if options.country:
                params["country"] = options.country.upper()
            
            if options.lang:
                params["language"] = options.lang.upper()
            
            # Handle time filtering
            if options.date_start and options.date_end:
                # Format: YYYY-MM-DDtoYYYY-MM-DD
                params["freshness"] = f"{options.date_start}to{options.date_end}"
            elif options.time_range:
                # Map TimeRange to freshness values: day, week, month, year
                freshness_map = {
                    "d": "day",
                    "w": "week",
                    "m": "month",
                    "y": "year"
                }
                params["freshness"] = freshness_map.get(options.time_range.value, "month")
            
            if options.extra_options:
                params.update(options.extra_options)
        
        return params

    def serp(self, query: str, page=None, num=None, options=None):
        params = self.get_serp_params(query, page, num, options)
        headers = {
            "X-API-Key": self.api_key,
        }
        resp = httpx.get(self.endpoint, params=params, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        items = self.parse_result(resp.json())
        return SerpResponse(items=items, cached=False)

    async def async_serp(self, query: str, page=None, num=None, options=None):
        params = self.get_serp_params(query, page, num, options)
        headers = {
            "X-API-Key": self.api_key,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(self.endpoint, params=params, headers=headers)
            resp.raise_for_status()
            items = self.parse_result(resp.json())
        return SerpResponse(items=items, cached=False)

    def parse_result(self, resp) -> List[SerpResult]:
        """
        Parse results from both web and news sections
        """
        results = []
        
        # Parse web results
        web_results = resp.get("results", {}).get("web", [])
        for item in web_results:
            # Join snippets if available, otherwise use description
            snippet = " ".join(item.get("snippets", [])) if item.get("snippets") else item.get("description", "")
            
            results.append(
                SerpResult(
                    title=item.get("title", ""),
                    link=item.get("url", ""),
                    snippet=snippet,
                    prefix=""
                )
            )
        
        # Parse news results
        news_results = resp.get("results", {}).get("news", [])
        for item in news_results:
            results.append(
                SerpResult(
                    title=item.get("title", ""),
                    link=item.get("url", ""),
                    snippet=item.get("description", ""),
                    prefix="[News]"
                )
            )
        
        return results
