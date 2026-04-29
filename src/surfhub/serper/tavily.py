from typing import List, Optional, Dict
from surfhub.serper.model import SerpResult, SerpResponse, BaseSerper, SerpRequestOptions


class TavilySerpResponse(SerpResponse):
    answer: Optional[str] = None


class Tavily(BaseSerper):
    """
    Search via Tavily API
    """
    default_api_url = "https://api.tavily.com/search"

    def get_serp_params(self, query: str, page=None, num=None, options: SerpRequestOptions = None) -> dict:
        params = {
            "query": query,
        }
        if num is not None:
            params["max_results"] = num
        
        if options:
            if options.date_start or options.date_end:
                if options.date_start:
                    params["start_date"] = options.date_start
                if options.date_end:
                    params["end_date"] = options.date_end
            elif options.time_range:
                params["time_range"] = options.time_range.value
            
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
            "Authorization": f"Bearer {self.api_key}",
        }

    def build_response(self, items: List[SerpResult], cached: bool, resp_data=None) -> TavilySerpResponse:
        answer = resp_data.get("answer", None) if resp_data else None
        return TavilySerpResponse(
            items=items,
            cached=cached,
            answer=answer,
        )

    def parse_result(self, resp: dict) -> List[SerpResult]:
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
