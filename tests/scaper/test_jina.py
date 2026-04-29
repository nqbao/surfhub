import respx
import httpx
import pytest
from surfhub.scraper.jina import JinaScraper

JINA_URL = "https://r.jina.ai/https://example.com"


def test_jina_scraper_basic_html():
    with respx.mock:
        respx.get(JINA_URL).mock(
            return_value=httpx.Response(
                200,
                headers={"content-type": "text/html; charset=utf-8"},
                text="<html><body>This is the page content from Jina.</body></html>",
            )
        )
        scraper = JinaScraper(api_key="test_key")
        resp = scraper.scrape("https://example.com")
        assert resp.content.decode(resp.encoding) == "<html><body>This is the page content from Jina.</body></html>"
        assert resp.final_url == "https://example.com"
        assert resp.status_code == 200


def test_jina_scraper_no_accept_header():
    with respx.mock:
        route = respx.get(JINA_URL).mock(
            return_value=httpx.Response(
                200,
                headers={"content-type": "text/html"},
                text="<html>content</html>",
            )
        )
        scraper = JinaScraper(api_key="test_key")
        scraper.scrape("https://example.com")
        assert "Accept" not in route.calls[0].request.headers


def test_jina_scraper_markdown_format():
    with respx.mock:
        route = respx.get(JINA_URL).mock(
            return_value=httpx.Response(
                200,
                headers={"content-type": "text/plain; charset=utf-8"},
                text="# markdown content",
            )
        )
        scraper = JinaScraper(api_key="test_key", format="markdown")
        scraper.scrape("https://example.com")
        assert route.calls[0].request.headers["X-Return-Format"] == "markdown"


def test_jina_scraper_text_format():
    with respx.mock:
        route = respx.get(JINA_URL).mock(
            return_value=httpx.Response(
                200,
                headers={"content-type": "text/plain; charset=utf-8"},
                text="plain text",
            )
        )
        scraper = JinaScraper(api_key="test_key", format="text")
        scraper.scrape("https://example.com")
        assert route.calls[0].request.headers["X-Return-Format"] == "text"


def test_jina_scraper_text_content():
    with respx.mock:
        respx.get(JINA_URL).mock(
            return_value=httpx.Response(
                200,
                headers={"content-type": "text/plain; charset=utf-8"},
                text="Hello World",
            )
        )
        scraper = JinaScraper(api_key="test_key", format="text")
        resp = scraper.scrape("https://example.com")
        assert resp.content.decode(resp.encoding) == "Hello World"
        assert resp.final_url == "https://example.com"


def test_jina_scraper_json_fallback():
    with respx.mock:
        respx.get(JINA_URL).mock(
            return_value=httpx.Response(
                200,
                headers={"content-type": "application/json"},
                json={
                    "data": {
                        "url": "https://example.com",
                        "content": "# Hello World",
                    }
                },
            )
        )
        scraper = JinaScraper(api_key="test_key", format="markdown")
        resp = scraper.scrape("https://example.com")
        assert resp.content.decode(resp.encoding) == "# Hello World"
        assert resp.final_url == "https://example.com"


def test_jina_scraper_json_fallback_empty_content():
    with respx.mock:
        respx.get(JINA_URL).mock(
            return_value=httpx.Response(
                200,
                headers={"content-type": "application/json; charset=utf-8"},
                json={"data": {"url": "https://example.com"}},
            )
        )
        scraper = JinaScraper(api_key="test_key", format="text")
        resp = scraper.scrape("https://example.com")
        assert resp.content.decode(resp.encoding) == '{"data":{"url":"https://example.com"}}'


def test_jina_scraper_invalid_format():
    with pytest.raises(ValueError, match="Invalid format"):
        JinaScraper(api_key="test_key", format="pdf")


def test_jina_scraper_default_engine_is_direct():
    with respx.mock:
        route = respx.get(JINA_URL).mock(
            return_value=httpx.Response(
                200,
                headers={"content-type": "text/html"},
                text="<html>content</html>",
            )
        )
        scraper = JinaScraper(api_key="test_key")
        scraper.scrape("https://example.com")
        assert route.calls[0].request.headers["X-Engine"] == "direct"


def test_jina_scraper_browser_engine():
    with respx.mock:
        route = respx.get(JINA_URL).mock(
            return_value=httpx.Response(
                200,
                headers={"content-type": "text/plain"},
                text="content",
            )
        )
        scraper = JinaScraper(api_key="test_key", engine="browser")
        scraper.scrape("https://example.com")
        assert route.calls[0].request.headers["X-Engine"] == "browser"


def test_jina_scraper_invalid_engine():
    with pytest.raises(ValueError, match="Invalid engine"):
        JinaScraper(api_key="test_key", engine="phantom")


def test_jina_scraper_auth_header():
    with respx.mock:
        route = respx.get("https://r.jina.ai/https://example.com").mock(
            return_value=httpx.Response(
                200,
                headers={"content-type": "text/plain"},
                text="content",
            )
        )
        scraper = JinaScraper(api_key="my_secret_key")
        scraper.scrape("https://example.com")
        assert route.calls[0].request.headers["Authorization"] == "Bearer my_secret_key"


def test_jina_scraper_no_auth():
    with respx.mock:
        route = respx.get("https://r.jina.ai/https://example.com").mock(
            return_value=httpx.Response(
                200,
                headers={"content-type": "text/plain"},
                text="content",
            )
        )
        scraper = JinaScraper()
        scraper.scrape("https://example.com")
        assert "Authorization" not in route.calls[0].request.headers


def test_jina_scraper_empty_content():
    with respx.mock:
        respx.get(JINA_URL).mock(
            return_value=httpx.Response(
                200,
                headers={"content-type": "text/plain"},
                text="",
            )
        )
        scraper = JinaScraper(api_key="test_key", format="markdown")
        resp = scraper.scrape("https://example.com")
        assert resp.content.decode(resp.encoding) == ""


@pytest.mark.anyio
async def test_jina_scraper_async():
    with respx.mock:
        respx.get("https://r.jina.ai/https://async.example.com").mock(
            return_value=httpx.Response(
                200,
                headers={"content-type": "text/plain"},
                text="async jina content",
            )
        )
        scraper = JinaScraper(api_key="test_key")
        resp = await scraper.async_scrape("https://async.example.com")
        assert resp.content.decode(resp.encoding) == "async jina content"
