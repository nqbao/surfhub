import respx
import httpx
import pytest
from surfhub.scraper.firecrawl import FirecrawlScraper

FIRECRAWL_URL = "https://api.firecrawl.dev/v1/scrape"


def test_firecrawl_scraper_basic():
    with respx.mock:
        respx.post(FIRECRAWL_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "success": True,
                    "data": {
                        "markdown": "This is the page content from Firecrawl.",
                        "metadata": {
                            "title": "Example",
                            "sourceURL": "https://example.com",
                        },
                    },
                },
            )
        )
        scraper = FirecrawlScraper(api_key="test_key")
        resp = scraper.scrape("https://example.com")
        assert resp.content.decode(resp.encoding) == "This is the page content from Firecrawl."
        assert resp.final_url == "https://example.com"
        assert resp.status_code == 200


def test_firecrawl_scraper_auth_header():
    with respx.mock:
        route = respx.post(FIRECRAWL_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "success": True,
                    "data": {"markdown": "content", "metadata": {"sourceURL": "https://example.com"}},
                },
            )
        )
        scraper = FirecrawlScraper(api_key="my_secret_key")
        scraper.scrape("https://example.com")
        assert route.calls[0].request.headers["Authorization"] == "Bearer my_secret_key"


def test_firecrawl_scraper_request_body():
    with respx.mock:
        route = respx.post(FIRECRAWL_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "success": True,
                    "data": {"markdown": "content", "metadata": {"sourceURL": "https://example.com"}},
                },
            )
        )
        scraper = FirecrawlScraper(api_key="test_key")
        scraper.scrape("https://example.com")
        import json

        body = json.loads(route.calls[0].request.content)
        assert body["url"] == "https://example.com"
        assert body["formats"] == ["markdown"]


def test_firecrawl_scraper_no_metadata():
    with respx.mock:
        respx.post(FIRECRAWL_URL).mock(
            return_value=httpx.Response(
                200,
                json={"success": True, "data": {"markdown": ""}},
            )
        )
        scraper = FirecrawlScraper(api_key="test_key")
        resp = scraper.scrape("https://example.com")
        assert resp.content.decode(resp.encoding) == ""
        assert resp.final_url == "https://example.com"


@pytest.mark.anyio
async def test_firecrawl_scraper_async():
    with respx.mock:
        respx.post(FIRECRAWL_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "success": True,
                    "data": {
                        "markdown": "async firecrawl content",
                        "metadata": {"sourceURL": "https://async.example.com"},
                    },
                },
            )
        )
        scraper = FirecrawlScraper(api_key="test_key")
        resp = await scraper.async_scrape("https://async.example.com")
        assert resp.content.decode(resp.encoding) == "async firecrawl content"
