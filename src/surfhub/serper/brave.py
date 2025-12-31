from typing import List
from surfhub.serper.model import SerpResult, BaseSerper, SerpResponse
import httpx


class BraveSearch(BaseSerper):
    """
    Search via Brave Search API
    https://api-dashboard.search.brave.com/app/documentation/web-search/get-started
    """
    default_api_url = "https://api.search.brave.com/res/v1/web/search"

    def get_serp_params(self, query, page=None, num=None, options=None):
        params = {
            "q": query,
        }
        
        if num is not None:
            params["count"] = num
        
        if page is not None:
            params["offset"] = page
        
        if options:
            if options.country:
                params["country"] = options.country.upper()
            
            if options.lang:
                params["search_lang"] = options.lang
            
            # Handle time filtering with freshness parameter
            if options.date_start and options.date_end:
                # Format: YYYY-MM-DDtoYYYY-MM-DD
                params["freshness"] = f"{options.date_start}to{options.date_end}"
            elif options.time_range:
                # Map TimeRange to freshness values: pd (day), pw (week), pm (month), py (year)
                freshness_map = {
                    "d": "pd",  # past day
                    "w": "pw",  # past week
                    "m": "pm",  # past month
                    "y": "py"   # past year
                }
                params["freshness"] = freshness_map.get(options.time_range.value, "pm")
            
            if options.extra_options:
                params.update(options.extra_options)
        
        return params

    def serp(self, query: str, page=None, num=None, options=None):
        params = self.get_serp_params(query, page, num, options)
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key,
        }
        resp = httpx.get(self.endpoint, params=params, headers=headers, timeout=self.timeout)
        items = self.parse_result(resp.json())
        return SerpResponse(items=items, cached=False)

    async def async_serp(self, query: str, page=None, num=None, options=None):
        params = self.get_serp_params(query, page, num, options)
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(self.endpoint, params=params, headers=headers)
            items = self.parse_result(resp.json())
        return SerpResponse(items=items, cached=False)

    def parse_result(self, resp) -> List[SerpResult]:
        """
        Parse results from web and news sections
        """
        results = []
        
        # Parse web search results
        web_results = resp.get("web", {}).get("results", [])
        for item in web_results:
            results.append(
                SerpResult(
                    title=item.get("title", ""),
                    link=item.get("url", ""),
                    snippet=item.get("description", ""),
                    prefix=""
                )
            )
        
        # Parse news results
        news_results = resp.get("news", {}).get("results", [])
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
