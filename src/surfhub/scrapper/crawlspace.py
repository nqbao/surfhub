from .model import BaseScrapper
import httpx

class CrawlspaceScrapper(BaseScrapper):
    """
    Scrapper that uses Crawlspace API
    
    Crawlspace uses different token for JS Scrapper and HTML Scrapper. You will need to provide the correct token.
    
    https://crawlbase.com/docs/crawling-api/response
    """
    default_api_url = "https://api.crawlbase.com/"
    
    def scrape(self, url, options = None) -> bytes:
        resp = httpx.get(
            self.endpoint,
            params={
                "token": self.api_key,
                "url": url,
            },
            timeout=self.timeout
        )

        if (resp.status_code != 200):
            raise Exception(f"Unexpetected error: " + resp.text)

        # check pc_status
        if resp.headers.get("pc_status") != "200":
            raise Exception(f"Unexpetected error: " + resp.text)

        # "finalUrl": resp.headers.get("url") or link,
        # "statusCode": str(resp.headers.get("original_status") or "200"),

        return resp.content
