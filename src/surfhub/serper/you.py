from typing import List, Dict
from surfhub.serper.model import SerpResult, BaseSerper, SerpRequestOptions


class YouSearch(BaseSerper):
    """
    Search via You.com API
    https://docs.you.com/api-reference/search/v1-search.md
    """
    default_api_url = "https://ydc-index.io/v1/search"

    def get_serp_params(self, query: str, page=None, num=None, options: SerpRequestOptions = None) -> dict:
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
            
            if options.date_start and options.date_end:
                params["freshness"] = f"{options.date_start}to{options.date_end}"
            elif options.time_range:
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

    @property
    def request_headers(self) -> Dict[str, str]:
        return {
            "X-API-Key": self.api_key,
        }

    def parse_result(self, resp: dict) -> List[SerpResult]:
        results = []
        
        web_results = resp.get("results", {}).get("web", [])
        for item in web_results:
            snippet = " ".join(item.get("snippets", [])) if item.get("snippets") else item.get("description", "")
            
            results.append(
                SerpResult(
                    title=item.get("title", ""),
                    link=item.get("url", ""),
                    snippet=snippet,
                    prefix=""
                )
            )
        
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
