from .model import BaseScraper, ScraperResponse
import httpx

VALID_FORMATS = {"html", "markdown", "text"}
VALID_ENGINES = {"direct", "browser", "cf-browser-rendering"}


class JinaScraper(BaseScraper):
    """
    Scraper that uses Jina.ai Reader API (https://jina.ai)
    Fetches cleaned page content for a given URL.
    Auth: Authorization: Bearer header (optional for free tier).

    Args:
        api_key: Jina.ai API key (optional for free tier).
        format: Return format — "html" (default), "markdown", or "text".
        engine: Rendering engine — "direct" (default, fast), "browser" (JS-heavy sites), "cf-browser-rendering" (experimental).
    """

    default_api_url = "https://r.jina.ai"

    def __init__(self, api_key: str = None, format: str = "html", engine: str = "direct"):
        super().__init__(api_key=api_key)
        if format not in VALID_FORMATS:
            raise ValueError(f"Invalid format '{format}'. Must be one of: {', '.join(sorted(VALID_FORMATS))}")
        if engine not in VALID_ENGINES:
            raise ValueError(f"Invalid engine '{engine}'. Must be one of: {', '.join(sorted(VALID_ENGINES))}")
        self._format = format
        self._engine = engine

    def prepare_request(self, url: str, options=None) -> httpx.Request:
        api_url = f"{self.api_url.rstrip('/')}/{url}"
        headers = {
            "X-Return-Format": self._format,
            "X-Engine": self._engine,
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return httpx.Request("GET", api_url, headers=headers)

    def parse_response(self, url: str, resp: httpx.Response) -> ScraperResponse:
        content_type = resp.headers.get("content-type", "")
        if "application/json" in content_type:
            data = resp.json()
            content = data.get("data", {}).get("content", "")
            if not content:
                content = resp.text
            final_url = data.get("data", {}).get("url", url)
        else:
            content = resp.text
            final_url = url
        return ScraperResponse(
            content=content.encode("utf-8"),
            final_url=final_url,
            status_code=resp.status_code,
        )
