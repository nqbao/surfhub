"""Integration test for universal markdown support (hits live endpoints).

Usage:
    python tests/integration/integtest_scraper_markdown.py
    pytest tests/integration/integtest_scraper_markdown.py
"""

import asyncio
from surfhub.scraper import get_scraper
from surfhub.scraper.model import ScraperResponse


def test_local_scraper_markdown():
    scraper = get_scraper("local")
    resp = scraper.scrape("https://example.com")
    assert resp.content_type == "text/html"
    assert resp.encoding in ("utf-8", "UTF-8")

    md = resp.markdown()
    assert len(md) > 0, "markdown should not be empty"
    assert "documentation" in md.lower(), "should contain page content"


def test_jina_markdown_pass_through():
    scraper = get_scraper("jina", format="markdown")
    resp = scraper.scrape("https://example.com")
    assert resp.content_type == "text/markdown"
    assert resp.encoding == "utf-8"

    md = resp.markdown()
    assert len(md) > 0, "markdown should not be empty"
    assert "Example" in md, "Jina markdown should contain page content"


def test_jina_html_to_markdown():
    scraper = get_scraper("jina", format="html")
    resp = scraper.scrape("https://example.com")
    assert "html" in resp.content_type

    md = resp.markdown()
    assert len(md) > 0, "markdown should not be empty"
    assert "documentation" in md.lower(), "trafilatura should extract main content"


def test_jina_text_pass_through():
    scraper = get_scraper("jina", format="text")
    resp = scraper.scrape("https://example.com")
    assert resp.content_type == "text/plain"

    md = resp.markdown()
    assert len(md) > 0, "markdown should not be empty"
    assert "Example" in md, "plain text should pass through"


def test_content_type_markdown_bypasses_trafilatura():
    resp = ScraperResponse(
        content=b"# Firecrawl Markdown\n\nSome content.",
        content_type="text/markdown",
        encoding="utf-8",
        final_url="https://example.com",
        status_code=200,
    )
    md = resp.markdown()
    assert md == "# Firecrawl Markdown\n\nSome content.", "markdown should pass through unchanged"


def test_content_type_plain_text_pass_through():
    resp = ScraperResponse(
        content=b"Just some plain text with special chars: \xc3\xa9",
        content_type="text/plain",
        encoding="utf-8",
        final_url="https://example.com",
        status_code=200,
    )
    md = resp.markdown()
    assert "special" in md, "plain text should pass through"


async def _run_async():
    print("Local scraper async...")
    scraper = get_scraper("local")
    resp = await scraper.async_scrape("https://example.com")
    md = resp.markdown()
    assert len(md) > 0, "markdown should not be empty"
    assert "documentation" in md.lower(), "should contain page content"
    print("  OK")

    print("Jina markdown async...")
    scraper = get_scraper("jina", format="markdown")
    resp = await scraper.async_scrape("https://example.com")
    assert resp.content_type == "text/markdown"
    md = resp.markdown()
    assert len(md) > 0, "markdown should not be empty"
    assert "Example" in md, "Jina markdown should contain page content"
    print("  OK")


if __name__ == "__main__":
    print("Local scraper markdown...")
    test_local_scraper_markdown()
    print("  OK")

    print("Jina markdown pass-through...")
    test_jina_markdown_pass_through()
    print("  OK")

    print("Jina HTML to markdown...")
    test_jina_html_to_markdown()
    print("  OK")

    print("Jina text pass-through...")
    test_jina_text_pass_through()
    print("  OK")

    print("Markdown bypasses trafilatura...")
    test_content_type_markdown_bypasses_trafilatura()
    print("  OK")

    print("Plain text pass-through...")
    test_content_type_plain_text_pass_through()
    print("  OK")

    asyncio.run(_run_async())

    print("\nAll integration tests passed!")
