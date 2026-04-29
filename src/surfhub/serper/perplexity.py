from typing import List, Optional, Dict
from surfhub.serper.model import SerpResult, SerpResponse, BaseSerper, SerpRequestOptions


class PerplexitySerpResponse(SerpResponse):
    answer: Optional[str] = None


class PerplexitySearch(BaseSerper):
    """
    Search via Perplexity Sonar API (https://perplexity.ai)
    Uses the chat completions endpoint with the sonar model for web search.
    """

    default_api_url = "https://api.perplexity.ai/chat/completions"

    def get_serp_params(self, query: str, page=None, num=None, options: SerpRequestOptions = None) -> dict:
        content = query
        if options:
            if options.date_start:
                content = f"{content} (after {options.date_start})"
            if options.date_end:
                content = f"{content} (before {options.date_end})"

        params = {
            "model": "sonar-pro",
            "messages": [
                {"role": "system", "content": "Be precise and concise. Always cite sources."},
                {"role": "user", "content": content},
            ],
        }

        if options and options.extra_options:
            for key, value in options.extra_options.items():
                if key not in ("model", "messages"):
                    params[key] = value

        return params

    @property
    def request_method(self) -> str:
        return "POST"

    @property
    def request_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def build_response(self, items: List[SerpResult], cached: bool, resp_data=None) -> PerplexitySerpResponse:
        answer = None
        if resp_data:
            choices = resp_data.get("choices", [])
            if choices:
                answer = choices[0].get("message", {}).get("content")
        return PerplexitySerpResponse(
            items=items,
            cached=cached,
            answer=answer,
        )

    def parse_result(self, resp: dict) -> List[SerpResult]:
        results = []
        citations = resp.get("citations", [])
        for url in citations:
            results.append(
                SerpResult(
                    title=url,
                    link=url,
                    snippet="",
                    prefix="",
                )
            )
        return results
