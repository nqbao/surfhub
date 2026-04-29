from .model import BaseScraper, ScraperResponse
import httpx


class ScrapingBeeScraper(BaseScraper):
    """
    Scraper that uses ScrapingBee API (https://scrapingbee.com)
    Fetches page content via a headless browser with JS rendering.
    Auth: api_key as a query parameter.

    Args:
        api_key: ScrapingBee API key.
        render_js: Use headless browser to render JS (default True).
        premium_proxy: Route through premium residential proxies (default False).
    """

    default_api_url = "https://app.scrapingbee.com/api/v1/"

    def __init__(self, api_key: str = None, render_js: bool = True, premium_proxy: bool = False):
        super().__init__(api_key=api_key)
        self._render_js = render_js
        self._premium_proxy = premium_proxy

    def prepare_request(self, url: str, options=None) -> httpx.Request:
        params = {
            "api_key": self.api_key,
            "url": url,
        }
        if not self._render_js:
            params["render_js"] = "false"
        if self._premium_proxy:
            params["premium_proxy"] = "true"
        return httpx.Request("GET", self.api_url, params=params)

    def parse_response(self, url: str, resp: httpx.Response) -> ScraperResponse:
        return ScraperResponse(
            content=resp.content,
            final_url=url,
            status_code=resp.status_code,
        )
