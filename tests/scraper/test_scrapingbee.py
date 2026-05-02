import respx
import httpx
import pytest
from surfhub.scraper.scrapingbee import ScrapingBeeScraper

SCRAPINGBEE_URL = "https://app.scrapingbee.com/api/v1/"


def test_scrapingbee_basic():
    with respx.mock:
        respx.get(SCRAPINGBEE_URL).mock(
            return_value=httpx.Response(
                200,
                headers={"content-type": "text/html"},
                text="<html><body>Scraped content</body></html>",
            )
        )
        scraper = ScrapingBeeScraper(api_key="test_key")
        resp = scraper.scrape("https://example.com")
        assert resp.content.decode(resp.encoding) == "<html><body>Scraped content</body></html>"
        assert resp.final_url == "https://example.com"
        assert resp.status_code == 200


def test_scrapingbee_query_params():
    with respx.mock:
        route = respx.get(SCRAPINGBEE_URL).mock(
            return_value=httpx.Response(
                200,
                headers={"content-type": "text/html"},
                text="<html>content</html>",
            )
        )
        scraper = ScrapingBeeScraper(api_key="test_key")
        scraper.scrape("https://example.com")
        request = route.calls[0].request
        assert request.url.params["api_key"] == "test_key"
        assert request.url.params["url"] == "https://example.com"


def test_scrapingbee_render_js_default():
    with respx.mock:
        route = respx.get(SCRAPINGBEE_URL).mock(
            return_value=httpx.Response(
                200,
                headers={"content-type": "text/html"},
                text="<html>content</html>",
            )
        )
        scraper = ScrapingBeeScraper(api_key="test_key")
        scraper.scrape("https://example.com")
        assert route.calls[0].request.url.params["render_js"] == "false"


def test_scrapingbee_use_browser():
    with respx.mock:
        route = respx.get(SCRAPINGBEE_URL).mock(
            return_value=httpx.Response(
                200,
                headers={"content-type": "text/html"},
                text="<html>content</html>",
            )
        )
        scraper = ScrapingBeeScraper(api_key="test_key")
        scraper.scrape("https://example.com", use_browser=True)
        assert "render_js" not in route.calls[0].request.url.params


def test_scrapingbee_premium_proxy():
    with respx.mock:
        route = respx.get(SCRAPINGBEE_URL).mock(
            return_value=httpx.Response(
                200,
                headers={"content-type": "text/html"},
                text="<html>content</html>",
            )
        )
        scraper = ScrapingBeeScraper(api_key="test_key", premium_proxy=True)
        scraper.scrape("https://example.com")
        assert route.calls[0].request.url.params["premium_proxy"] == "true"


def test_scrapingbee_binary_content():
    with respx.mock:
        respx.get(SCRAPINGBEE_URL).mock(
            return_value=httpx.Response(
                200,
                headers={"content-type": "application/pdf"},
                content=b"%PDF-1.4 fake pdf content",
            )
        )
        scraper = ScrapingBeeScraper(api_key="test_key")
        resp = scraper.scrape("https://example.com/doc.pdf")
        assert resp.content == b"%PDF-1.4 fake pdf content"


@pytest.mark.anyio
async def test_scrapingbee_async():
    with respx.mock:
        respx.get(SCRAPINGBEE_URL).mock(
            return_value=httpx.Response(
                200,
                headers={"content-type": "text/html"},
                text="<html>async scrapingbee content</html>",
            )
        )
        scraper = ScrapingBeeScraper(api_key="test_key")
        resp = await scraper.async_scrape("https://async.example.com")
        assert resp.content.decode(resp.encoding) == "<html>async scrapingbee content</html>"
