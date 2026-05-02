from .model import BaseScraper, ScraperResponse
import httpx

class ZyteScraper(BaseScraper):
    """
    Scraper that uses Zyte Extract API
    """
    default_api_url = "https://api.zyte.com/v1/extract"
    
    def prepare_request(self, url, options=None, use_browser: bool = False) -> httpx.Request:
        return httpx.Request(
            "POST", 
            self.api_url,
            json={
                "url": url,  
                "browserHtml": use_browser,
            }
        )
        
    def get_request_auth(self) -> tuple:
        return (self.api_key, "")
        
    def parse_response(self, url: str, resp: httpx.Response) -> ScraperResponse:
        data = resp.json()
        content = data.get("browserHtml") or data.get("httpResponseBody", b"").decode("utf-8")
        
        return ScraperResponse(
            content=content,
            content_type="text/html",
            encoding="utf-8",
            final_url=url,
            status_code=resp.status_code,
        )
