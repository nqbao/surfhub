from .model import BaseScrapper, ScrapperResponse
import httpx

class CrawlbaseScrapper(BaseScrapper):
    """
    Scrapper that uses Crawlbase API
    
    Crawlspace uses different token for JS Scrapper and HTML Scrapper. You will need to provide the correct token.
    
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
        
    def parse_response(self, url, resp: httpx.Response) -> ScrapperResponse:
        # check pc_status
        if resp.headers.get("pc_status") != "200":
            raise Exception("Unexpetected error: " + resp.text)
        
        return ScrapperResponse(
            content=resp.content,
            final_url=resp.headers.get("url") or url,
            status_code=str(resp.headers.get("original_status") or "200"),
        )
