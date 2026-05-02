from .model import BaseScraper, ScraperResponse
import httpx

VALID_FORMATS = {"html", "markdown", "text"}


class JinaScraper(BaseScraper):
    """
    Scraper that uses Jina.ai Reader API (https://jina.ai)
    Fetches cleaned page content for a given URL.
    Auth: Authorization: Bearer header (optional for free tier).

    Args:
        api_key: Jina.ai API key (optional for free tier).
        format: Return format — "html" (default), "markdown", or "text".
    """

    default_api_url = "https://r.jina.ai"

    def __init__(self, api_key: str = None, format: str = "html"):
        super().__init__(api_key=api_key)
        if format not in VALID_FORMATS:
            raise ValueError(f"Invalid format '{format}'. Must be one of: {', '.join(sorted(VALID_FORMATS))}")
        self._format = format

    def prepare_request(self, url: str, options=None, use_browser: bool = False) -> httpx.Request:
        api_url = f"{self.api_url.rstrip('/')}/{url}"
        headers = {
            "X-Return-Format": self._format,
            "X-Engine": "browser" if use_browser else "direct",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return httpx.Request("GET", api_url, headers=headers)

    def parse_response(self, url: str, resp: httpx.Response) -> ScraperResponse:
        resp_content_type = resp.headers.get("content-type", "")
        if "application/json" in resp_content_type:
            data = resp.json()
            content = data.get("data", {}).get("content", "")
            if not content:
                content = resp.text
            final_url = data.get("data", {}).get("url", url)
        else:
            content = resp.text
            final_url = url

        ct_map = {"html": "text/html", "markdown": "text/markdown", "text": "text/plain"}
        content_type = ct_map.get(self._format, "text/html")

        return ScraperResponse(
            content=content.encode("utf-8"),
            content_type=content_type,
            encoding="utf-8",
            final_url=final_url,
            status_code=resp.status_code,
        )
