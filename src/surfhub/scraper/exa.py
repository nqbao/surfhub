import json
from .model import BaseScraper, ScraperResponse
import httpx


class ExaScraper(BaseScraper):
    """
    Scraper that uses Exa Contents API (https://exa.ai)
    Fetches cleaned page text for a given URL via POST /contents.
    Auth: x-api-key header.
    """

    default_api_url = "https://api.exa.ai/contents"

    def prepare_request(self, url: str, options=None, use_browser: bool = False) -> httpx.Request:
        return httpx.Request(
            "POST",
            self.api_url,
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
            },
            content=json.dumps(
                {
                    "ids": [url],
                    "text": True,
                }
            ).encode(),
        )

    def parse_response(self, url: str, resp: httpx.Response) -> ScraperResponse:
        data = resp.json()
        results = data.get("results", [])
        text = results[0].get("text", "") if results else ""
        final_url = results[0].get("url", url) if results else url
        return ScraperResponse(
            content=text.encode("utf-8"),
            content_type="text/plain",
            encoding="utf-8",
            final_url=final_url,
            status_code=resp.status_code,
        )
