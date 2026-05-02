"""Integration test for local browser rendering (hits live endpoints, requires Playwright).

Usage:
    python tests/integration/integtest_local_browser.py
    pytest tests/integration/integtest_local_browser.py
"""

import asyncio
from surfhub.scraper import get_scraper
from surfhub.scraper.model import ScraperOptions


def test_local_browser_basic():
    scraper = get_scraper("local")
    resp = scraper.scrape("https://example.com", use_browser=True)
    assert resp.status_code == 200
    assert resp.content_type == "text/html"
    assert resp.encoding == "utf-8"
    assert len(resp.content) > 0

    md = resp.markdown()
    assert len(md) > 0


def test_local_browser_with_networkidle():
    scraper = get_scraper("local")
    options = ScraperOptions(wait_until="networkidle")
    resp = scraper.scrape("https://example.com", options=options, use_browser=True)
    assert resp.status_code == 200
    assert resp.content_type == "text/html"
    assert len(resp.content) > 0


def test_local_browser_vs_http():
    scraper = get_scraper("local")

    http_resp = scraper.scrape("https://example.com", use_browser=False)
    browser_resp = scraper.scrape("https://example.com", use_browser=True)

    assert http_resp.status_code == 200
    assert browser_resp.status_code == 200
    assert http_resp.content_type == "text/html"
    assert browser_resp.content_type == "text/html"


async def _run_async():
    print("Local browser async...")
    scraper = get_scraper("local")
    resp = await scraper.async_scrape("https://example.com", use_browser=True)
    assert resp.status_code == 200
    assert resp.content_type == "text/html"
    assert resp.encoding == "utf-8"
    md = resp.markdown()
    assert len(md) > 0
    print("  OK")


if __name__ == "__main__":
    print("Local browser basic...")
    test_local_browser_basic()
    print("  OK")

    print("Local browser networkidle...")
    test_local_browser_with_networkidle()
    print("  OK")

    print("Local browser vs HTTP...")
    test_local_browser_vs_http()
    print("  OK")

    asyncio.run(_run_async())

    print("\nAll integration tests passed!")
