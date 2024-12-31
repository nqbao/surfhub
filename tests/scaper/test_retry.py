import respx
import httpx
from surfhub.scraper import ZyteScraper


def test_retry():
    with respx.mock:
        call = 0
        def response(_):
            nonlocal call
            call += 1
            
            if call == 1:
                raise httpx.ConnectError("Failed to connect")
                
            if call == 2:
                return httpx.Response(520)
            
            return httpx.Response(
                200, 
                json={
                    "browserHtml": "<html><body>Hello World</body></html>"
                }
            )
        
        route = respx.post("https://api.zyte.com/v1/extract")
        route.side_effect = response
        
        scaper = ZyteScraper(api_key="123456")
        resp = scaper.scrape("hello world")
        assert "Hello" in resp.content.decode("utf-8")
        assert call == 3
