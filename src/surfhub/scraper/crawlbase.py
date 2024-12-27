from .model import BaseScraper, ScraperResponse
import httpx

class CrawlbaseScraper(BaseScraper):
    """
    Scraper that uses Crawlbase API
    
    Crawlspace uses different token for JS Scraper and HTML Scraper. You will need to provide the correct token.
    
    https://crawlbase.com/docs/crawling-api/response
    """
    default_api_url = "https://api.crawlbase.com/"
    
    def prepare_request(self, url, options = None) -> httpx.Request:
        return httpx.Request(
            "GET", 
            self.api_url, 
            params={
                "token": self.api_key,
                "url": url,
            },
        )
        
    def validate_response(self, resp: httpx.Response):
        super().validate_response(resp)
        
        if resp.headers.get("pc_status") != "200":
            raise Exception("Unexpetected error: " + resp.text)

        
    def parse_response(self, url, resp: httpx.Response) -> ScraperResponse:
        return ScraperResponse(
            content=resp.content,
            final_url=resp.headers.get("url") or url,
            status_code=str(resp.headers.get("original_status") or "200"),
        )
