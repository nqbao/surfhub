import respx
import httpx
import pytest
from surfhub.scraper.exa import ExaScraper

EXA_CONTENTS_URL = "https://api.exa.ai/contents"


def test_exa_scraper_basic():
    with respx.mock:
        respx.post(EXA_CONTENTS_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "url": "https://example.com",
                            "text": "This is the page content.",
                        }
                    ]
                },
            )
        )
        scraper = ExaScraper(api_key="test_key")
        resp = scraper.scrape("https://example.com")
        assert resp.content.decode(resp.encoding) == "This is the page content."
        assert resp.final_url == "https://example.com"
        assert resp.status_code == 200


def test_exa_scraper_auth_header():
    with respx.mock:
        route = respx.post(EXA_CONTENTS_URL).mock(
            return_value=httpx.Response(
                200,
                json={"results": [{"url": "https://example.com", "text": "content"}]},
            )
        )
        scraper = ExaScraper(api_key="my_secret_key")
        scraper.scrape("https://example.com")
        assert route.calls[0].request.headers["x-api-key"] == "my_secret_key"


def test_exa_scraper_request_body():
    with respx.mock:
        route = respx.post(EXA_CONTENTS_URL).mock(
            return_value=httpx.Response(
                200,
                json={"results": [{"url": "https://example.com", "text": "content"}]},
            )
        )
        scraper = ExaScraper(api_key="test_key")
        scraper.scrape("https://example.com")
        import json

        body = json.loads(route.calls[0].request.content)
        assert body["ids"] == ["https://example.com"]
        assert body["text"] is True


def test_exa_scraper_empty_results():
    with respx.mock:
        respx.post(EXA_CONTENTS_URL).mock(return_value=httpx.Response(200, json={"results": []}))
        scraper = ExaScraper(api_key="test_key")
        resp = scraper.scrape("https://example.com")
        assert resp.content.decode(resp.encoding) == ""
        assert resp.final_url == "https://example.com"


@pytest.mark.anyio
async def test_exa_scraper_async():
    with respx.mock:
        respx.post(EXA_CONTENTS_URL).mock(
            return_value=httpx.Response(
                200,
                json={"results": [{"url": "https://async.example.com", "text": "async content"}]},
            )
        )
        scraper = ExaScraper(api_key="test_key")
        resp = await scraper.async_scrape("https://async.example.com")
        assert resp.content.decode(resp.encoding) == "async content"
