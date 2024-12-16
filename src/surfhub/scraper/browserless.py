from .model import BaseScrapper, ScrapperResponse
import httpx

class BrowserlessScrapper(BaseScrapper):
    """
    Scrapper that uses Browserless API
    
    https://docs.browserless.io/http-apis/scrape
    """
    default_api_url = "https://chrome.browserless.io"
    
    def prepare_request(self, url, options = None):
        # TODO: we can also use the /content api
        api_url = self.api_url + "/scrape?token=" + self.api_key
        return httpx.Request(
            "POST", 
            api_url,
            json={
                "url": url,
                "elements": [{"selector": "html"}],
                "waitFor": self.timeout
            }
        )
        
    def parse_response(self, url, resp):
        html = resp.json()['data'][0]['results'][0]['html']
        return ScrapperResponse(
            content=html.encode("utf-8"),
            final_url=url,
            status_code=resp.status_code
        )
