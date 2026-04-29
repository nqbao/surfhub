from typing import List, Optional, Dict
from surfhub.serper.model import SerpResult, BaseSerper, SerpRequestOptions


class ExaSearch(BaseSerper):
    """
    Search via Exa API (https://exa.ai)
    Uses neural/keyword/auto search and returns structured results.
    Auth: x-api-key header.
    """
    default_api_url = "https://api.exa.ai/search"

    def get_serp_params(self, query: str, page=None, num=None, options: SerpRequestOptions = None) -> dict:
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

    @property
    def request_method(self) -> str:
        return "POST"

    @property
    def request_headers(self) -> Dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def parse_result(self, resp: dict) -> List[SerpResult]:
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
