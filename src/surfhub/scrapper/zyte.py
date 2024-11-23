from .model import BaseScrapper
import httpx

class ZyteScrapper(BaseScrapper):
    """
    Scrapper that uses Zyte Extract API
    """
    default_api_url = "https://api.zyte.com/v1/extract"
    
    def scrape(self, url, options = None) -> bytes:
        resp = httpx.post(
            self.endpoint,
            auth=(self.api_key, ""),
            timeout=self.timeout,
            json={
                "url": url,  
                "browserHtml": True,
            },
        )
        
        if resp.status_code > 299:
            raise Exception("Unexpected status code: " + str(resp.status_code))

        return resp.json()['browserHtml'].encode("utf-8")
