import sys
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
import respx

from surfhub.scraper.local import LocalScraper
from surfhub.scraper.model import ScraperOptions


def _create_mock_playwright_module():
    mock_sync_api = MagicMock()
    mock_async_api = MagicMock()
    mock_module = MagicMock()
    mock_module.sync_api = mock_sync_api
    mock_module.async_api = mock_async_api
    return mock_module, mock_sync_api, mock_async_api


class TestLocalScraperHttp:
    def test_basic(self):
        with respx.mock:
            respx.get("https://example.com").mock(
                return_value=httpx.Response(200, text="<html>hello</html>"),
            )
            scraper = LocalScraper()
            resp = scraper.scrape("https://example.com")
            assert resp.content.decode() == "<html>hello</html>"
            assert resp.status_code == 200
            assert resp.final_url == "https://example.com"

    def test_use_browser_false_uses_http(self):
        with respx.mock:
            respx.get("https://example.com").mock(
                return_value=httpx.Response(200, text="<html>httpx</html>"),
            )
            scraper = LocalScraper()
            resp = scraper.scrape("https://example.com", use_browser=False)
            assert resp.content.decode() == "<html>httpx</html>"

    @pytest.mark.anyio
    async def test_async(self):
        with respx.mock:
            respx.get("https://example.com").mock(
                return_value=httpx.Response(200, text="<html>async</html>"),
            )
            scraper = LocalScraper()
            resp = await scraper.async_scrape("https://example.com")
            assert resp.content.decode() == "<html>async</html>"


class TestLocalScraperBrowser:
    @staticmethod
    def _setup_mock_sync(mock_sync_api, html="<html>rendered</html>", url="https://example.com"):
        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_page.url = url
        mock_page.content.return_value = html
        mock_browser.new_page.return_value = mock_page
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_sync_api.sync_playwright.return_value.__enter__.return_value = mock_playwright
        return mock_page

    @staticmethod
    def _setup_mock_async(mock_async_api, html="<html>async rendered</html>", url="https://example.com"):
        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_page.url = url
        mock_page.content = AsyncMock(return_value=html)
        mock_page.goto = AsyncMock()
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        mock_browser.close = AsyncMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_async_api.async_playwright.return_value.__aenter__.return_value = mock_playwright
        return mock_page

    def _install_mock_playwright(self):
        mock_module, mock_sync_api, mock_async_api = _create_mock_playwright_module()
        sys.modules["playwright"] = mock_module
        sys.modules["playwright.sync_api"] = mock_sync_api
        sys.modules["playwright.async_api"] = mock_async_api
        return mock_sync_api, mock_async_api

    def _uninstall_mock_playwright(self):
        sys.modules.pop("playwright", None)
        sys.modules.pop("playwright.sync_api", None)
        sys.modules.pop("playwright.async_api", None)

    def test_use_browser_true(self):
        mock_sync_api, _ = self._install_mock_playwright()
        try:
            mock_page = self._setup_mock_sync(mock_sync_api)

            scraper = LocalScraper()
            resp = scraper.scrape("https://example.com", use_browser=True)

            assert resp.content.decode() == "<html>rendered</html>"
            assert resp.content_type == "text/html"
            assert resp.encoding == "utf-8"
            assert resp.status_code == 200
            assert resp.final_url == "https://example.com"
            mock_page.goto.assert_called_once_with("https://example.com", wait_until="load", timeout=30000)
        finally:
            self._uninstall_mock_playwright()

    def test_timeout_converted_to_ms(self):
        mock_sync_api, _ = self._install_mock_playwright()
        try:
            mock_page = self._setup_mock_sync(mock_sync_api)

            scraper = LocalScraper()
            scraper.timeout = 60
            scraper.scrape("https://example.com", use_browser=True)

            mock_page.goto.assert_called_once_with("https://example.com", wait_until="load", timeout=60000)
        finally:
            self._uninstall_mock_playwright()

    def test_wait_until_from_options(self):
        mock_sync_api, _ = self._install_mock_playwright()
        try:
            mock_page = self._setup_mock_sync(mock_sync_api)

            scraper = LocalScraper()
            options = ScraperOptions(wait_until="networkidle")
            scraper.scrape("https://example.com", options=options, use_browser=True)

            mock_page.goto.assert_called_once_with("https://example.com", wait_until="networkidle", timeout=30000)
        finally:
            self._uninstall_mock_playwright()

    def test_wait_until_domcontentloaded(self):
        mock_sync_api, _ = self._install_mock_playwright()
        try:
            mock_page = self._setup_mock_sync(mock_sync_api)

            scraper = LocalScraper()
            options = ScraperOptions(wait_until="domcontentloaded")
            scraper.scrape("https://example.com", options=options, use_browser=True)

            mock_page.goto.assert_called_once_with("https://example.com", wait_until="domcontentloaded", timeout=30000)
        finally:
            self._uninstall_mock_playwright()

    def test_default_wait_until_load(self):
        mock_sync_api, _ = self._install_mock_playwright()
        try:
            mock_page = self._setup_mock_sync(mock_sync_api)

            scraper = LocalScraper()
            scraper.scrape("https://example.com", use_browser=True)

            mock_page.goto.assert_called_once_with("https://example.com", wait_until="load", timeout=30000)
        finally:
            self._uninstall_mock_playwright()

    @pytest.mark.anyio
    async def test_async_use_browser_true(self):
        _, mock_async_api = self._install_mock_playwright()
        try:
            mock_page = self._setup_mock_async(mock_async_api)

            scraper = LocalScraper()
            resp = await scraper.async_scrape("https://example.com", use_browser=True)

            assert resp.content.decode() == "<html>async rendered</html>"
            assert resp.content_type == "text/html"
            assert resp.encoding == "utf-8"
            assert resp.status_code == 200
            assert resp.final_url == "https://example.com"
            mock_page.goto.assert_awaited_once_with("https://example.com", wait_until="load", timeout=30000)
        finally:
            self._uninstall_mock_playwright()
