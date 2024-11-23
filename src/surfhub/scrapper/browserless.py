from .model import BaseScrapper
import httpx

class BrowserlessScrapper(BaseScrapper):
    """
    Scrapper that uses Browserless API
    
    https://docs.browserless.io/http-apis/scrape
    """
    default_api_url = "https://chrome.browserless.io/scrape"
    
    def scrape(self, url, options = None) -> bytes:
        api_url = self.endpoint + "?token=" + self.api_key
        resp = httpx.post(api_url, json={
            "url": url,
            "elements": [{"selector": "body"}],
            "waitFor": self.timeout
        }, timeout=self.timeout)
        
        if resp.status_code > 299:
            raise Exception("Unexpected status code: " + str(resp.status_code))
        
        return resp.json()['data'][0]['results'][0]['html'].encode("utf-8")
