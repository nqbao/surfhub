import pytest
from surfhub.scraper import get_scraper
from surfhub.scraper.model import ScraperResponse


@pytest.mark.integration
class TestMarkdownIntegration:
    def test_local_scraper_markdown(self):
        scraper = get_scraper("local")
        resp = scraper.scrape("https://example.com")
        assert resp.content_type == "text/html"
        assert resp.encoding in ("utf-8", "UTF-8")

        md = resp.markdown()
        assert len(md) > 0
        assert "documentation" in md.lower()

    @pytest.mark.anyio
    async def test_local_scraper_markdown_async(self):
        scraper = get_scraper("local")
        resp = await scraper.async_scrape("https://example.com")

        md = resp.markdown()
        assert len(md) > 0
        assert "documentation" in md.lower()

    def test_jina_markdown_pass_through(self):
        scraper = get_scraper("jina", format="markdown")
        resp = scraper.scrape("https://example.com")
        assert resp.content_type == "text/markdown"
        assert resp.encoding == "utf-8"

        md = resp.markdown()
        assert len(md) > 0
        assert "Example" in md

    @pytest.mark.anyio
    async def test_jina_markdown_pass_through_async(self):
        scraper = get_scraper("jina", format="markdown")
        resp = await scraper.async_scrape("https://example.com")
        assert resp.content_type == "text/markdown"

        md = resp.markdown()
        assert len(md) > 0
        assert "Example" in md

    def test_jina_html_to_markdown(self):
        scraper = get_scraper("jina", format="html")
        resp = scraper.scrape("https://example.com")
        assert "html" in resp.content_type

        md = resp.markdown()
        assert len(md) > 0
        # trafilatura extracts main content; title may or may not be included
        assert "documentation" in md.lower()

    def test_jina_text_pass_through(self):
        scraper = get_scraper("jina", format="text")
        resp = scraper.scrape("https://example.com")
        assert resp.content_type == "text/plain"

        md = resp.markdown()
        assert len(md) > 0
        assert "Example" in md

    def test_content_type_markdown_bypasses_trafilatura(self):
        resp = ScraperResponse(
            content=b"# Firecrawl Markdown\n\nSome content.",
            content_type="text/markdown",
            encoding="utf-8",
            final_url="https://example.com",
            status_code=200,
        )
        md = resp.markdown()
        assert md == "# Firecrawl Markdown\n\nSome content."

    def test_content_type_plain_text_pass_through(self):
        resp = ScraperResponse(
            content=b"Just some plain text with special chars: \xc3\xa9",
            content_type="text/plain",
            encoding="utf-8",
            final_url="https://example.com",
            status_code=200,
        )
        md = resp.markdown()
        assert "special" in md
