from typing import List, Dict
from surfhub.serper.model import SerpResult, BaseSerper, SerpRequestOptions


class JinaSearch(BaseSerper):
    """
    Search via Jina.ai Search API (https://s.jina.ai)
    Returns SERP results optimized for LLMs with title, description, url, and content.
    """

    default_api_url = "https://s.jina.ai"

    def get_serp_params(self, query: str, page=None, num=None, options: SerpRequestOptions = None) -> dict:
        params = {"q": query}

        if num is not None:
            params["num"] = num

        if page is not None:
            params["page"] = page

        if options:
            if options.lang:
                params["hl"] = options.lang

            if options.country:
                params["gl"] = options.country.lower()

            if options.location:
                params["location"] = options.location

            if options.date_start:
                params["date_start"] = options.date_start

            if options.date_end:
                params["date_end"] = options.date_end

            if options.extra_options:
                params.update(options.extra_options)

        return params

    @property
    def request_method(self) -> str:
        return "POST"

    @property
    def request_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Respond-With": "no-content",
            "Authorization": f"Bearer {self.api_key}",
        }

    def parse_result(self, resp: dict) -> List[SerpResult]:
        results = resp.get("data", [])
        if not isinstance(results, list):
            results = []

        print(f"Raw Jina API response: {resp}")
        return [
            SerpResult(
                title=r.get("title", ""),
                link=r.get("url", ""),
                snippet=r.get("description", ""),
                prefix="",
            )
            for r in results
        ]
