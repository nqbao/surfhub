import json
from .model import BaseScraper, ScraperResponse
import httpx


class FirecrawlScraper(BaseScraper):
    """
    Scraper that uses Firecrawl API (https://firecrawl.dev)
    Fetches cleaned page content as markdown for a given URL via POST /v1/scrape.
    Auth: Authorization: Bearer header.
    """

    default_api_url = "https://api.firecrawl.dev/v1/scrape"

    def prepare_request(self, url: str, options=None) -> httpx.Request:
        return httpx.Request(
            "POST",
            self.api_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            content=json.dumps({
                "url": url,
                "formats": ["markdown"],
            }).encode(),
        )

    def parse_response(self, url: str, resp: httpx.Response) -> ScraperResponse:
        data = resp.json()
        result = data.get("data", {})
        content = result.get("markdown", "")
        final_url = result.get("metadata", {}).get("sourceURL", url)
        return ScraperResponse(
            content=content.encode("utf-8"),
            content_type="text/markdown",
            encoding="utf-8",
            final_url=final_url,
            status_code=resp.status_code,
        )
