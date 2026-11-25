from unittest.mock import Mock

import httpx
import pytest
import respx
import trafilatura

from surfhub import get_scraper
from surfhub.scraper.jina import JinaScraper
from surfhub.scraper.local import LocalScraper
from surfhub.scraper.model import ScraperResponse


def response(content, content_type):
    return ScraperResponse(
        content=content, content_type=content_type, status_code=200, final_url="https://example.com"
    )


@pytest.mark.parametrize("content_type", ["application/pdf", "image/png", "application/octet-stream", ""])
def test_binary_content_returns_empty(content_type):
    engine = Mock()
    assert response(b"\xff\xfe\x00", content_type).markdown(engine=engine) == ""
    engine.assert_not_called()


@pytest.mark.parametrize("content_type", ["Text/Markdown; charset=utf-8", "application/json", "application/problem+json"])
def test_text_formats_pass_through(content_type):
    engine = Mock()
    assert response(b"original text", content_type).markdown(engine=engine) == "original text"
    engine.assert_not_called()


def test_custom_engine_receives_raw_html():
    html = b"<h1>Page</h1>"
    engine = Mock(return_value="# Page")
    assert response(html, "application/xhtml+xml; charset=utf-8").markdown(engine=engine) == "# Page"
    engine.assert_called_once_with(html)


@pytest.mark.parametrize("html", [b"  <HTML lang='en'>", b"\xef\xbb\xbf\n<!DOCTYPE html><body>"])
def test_missing_content_type_recognizes_html(html):
    engine = Mock(return_value="# Page")
    assert response(html, "").markdown(engine=engine) == "# Page"
    engine.assert_called_once_with(html)


@pytest.mark.parametrize("content_type", ["", "application/pdf"])
def test_html_sniff_does_not_override_binary_content(content_type):
    engine = Mock()
    assert response(b"%PDF-1.7\n<html><body>embedded</body></html>", content_type).markdown(engine=engine) == ""
    engine.assert_not_called()


def test_local_constructor_engine_with_per_call_override():
    url = "https://example.com"
    html = b"<h1>Page</h1>"
    engine = Mock(return_value="# Default")
    scraper = LocalScraper(markdown_engine=engine)
    with respx.mock:
        respx.get(url).respond(200, headers={"Content-Type": "text/html"}, content=html)
        page = scraper.scrape(url)

    assert page.markdown(engine=lambda _: "# Override") == "# Override"
    engine.assert_not_called()
    assert page.markdown() == "# Default"
    engine.assert_called_once_with(html)
    assert "_markdown_engine" not in page.model_dump()


@pytest.mark.anyio
@pytest.mark.parametrize("from_factory", [True, False])
async def test_hosted_scraper_uses_constructor_engine(from_factory):
    url = "https://example.com"
    engine = Mock(return_value="# Custom")
    scraper = get_scraper("jina", markdown_engine=engine) if from_factory else JinaScraper(markdown_engine=engine)
    with respx.mock:
        respx.get(f"https://r.jina.ai/{url}").mock(return_value=httpx.Response(200, text="<h1>Page</h1>"))
        page = await scraper.async_scrape(url)

    assert page.markdown() == "# Custom"
    engine.assert_called_once_with(b"<h1>Page</h1>")


def test_html_retries_with_favor_recall(monkeypatch):
    extract = Mock(side_effect=[None, "# Recovered"])
    monkeypatch.setattr(trafilatura, "extract", extract)
    assert response(b"<h1>Recovered</h1>", "text/html").markdown() == "# Recovered"
    assert [call.kwargs["favor_recall"] for call in extract.call_args_list] == [False, True]


@pytest.mark.parametrize(
    ("html", "expected"),
    [(b"<html><body><div>Sign in</div></body></html>", "Sign in"), (b"<html><body></body></html>", "")],
)
def test_html_falls_back_to_plain_text_and_never_source(monkeypatch, html, expected):
    monkeypatch.setattr(trafilatura, "extract", Mock(return_value=None))
    assert response(html, "text/html").markdown() == expected
