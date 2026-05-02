from typing import List, Dict
from surfhub.serper.model import SerpResult, BaseSerper, SerpRequestOptions


class BraveSearch(BaseSerper):
    """
    Search via Brave Search API
    https://api-dashboard.search.brave.com/app/documentation/web-search/get-started
    """

    default_api_url = "https://api.search.brave.com/res/v1/web/search"

    def get_serp_params(self, query: str, page=None, num=None, options: SerpRequestOptions = None) -> dict:
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

            if options.date_start and options.date_end:
                params["freshness"] = f"{options.date_start}to{options.date_end}"
            elif options.time_range:
                freshness_map = {"d": "pd", "w": "pw", "m": "pm", "y": "py"}
                params["freshness"] = freshness_map.get(options.time_range.value, "pm")

            if options.extra_options:
                params.update(options.extra_options)

        return params

    @property
    def request_headers(self) -> Dict[str, str]:
        return {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key,
        }

    def parse_result(self, resp: dict) -> List[SerpResult]:
        results = []

        web_results = resp.get("web", {}).get("results", [])
        for item in web_results:
            results.append(
                SerpResult(
                    title=item.get("title", ""),
                    link=item.get("url", ""),
                    snippet=item.get("description", ""),
                    prefix="",
                )
            )

        news_results = resp.get("news", {}).get("results", [])
        for item in news_results:
            results.append(
                SerpResult(
                    title=item.get("title", ""),
                    link=item.get("url", ""),
                    snippet=item.get("description", ""),
                    prefix="[News]",
                )
            )

        return results
