from .model import Scraper, ScraperOptions, ScraperResponse
import httpx


class LocalScraper(Scraper):
    _http_proxy: str = ""
    _https_proxy: str = ""
    _verify_ca: bool = True

    """
    A scraper that runs on local
    """

    def _get_proxies(self) -> dict | None:
        if self.http_proxy or self.https_proxy:
            return {
                "http://": self.http_proxy,
                "https://": self.https_proxy,
            }
        return None

    def scrape(self, url: str, options: ScraperOptions = None, use_browser: bool = False) -> ScraperResponse:
        if use_browser:
            return self._scrape_with_browser(url, options)

        proxies = self._get_proxies()
        resp = httpx.get(
            url,
            timeout=self.timeout,
            proxy=proxies,
            verify=self.verify_ca,
        )

        return ScraperResponse(
            content=resp.content,
            content_type=resp.headers.get("content-type", ""),
            encoding=resp.encoding or "utf-8",
            status_code=resp.status_code,
            final_url=str(resp.url),
        )

    async def async_scrape(self, url: str, options: ScraperOptions = None, use_browser: bool = False) -> ScraperResponse:
        if use_browser:
            return await self._async_scrape_with_browser(url, options)

        proxies = self._get_proxies()
        async with httpx.AsyncClient(proxy=proxies, verify=self.verify_ca) as client:
            resp = await client.get(
                url,
                timeout=self.timeout,
            )

        return ScraperResponse(
            content=resp.content,
            content_type=resp.headers.get("content-type", ""),
            encoding=resp.encoding or "utf-8",
            status_code=resp.status_code,
            final_url=str(resp.url),
        )

    def _scrape_with_browser(self, url: str, options: ScraperOptions = None) -> ScraperResponse:
        from playwright.sync_api import sync_playwright

        wait_until = self._get_wait_until(options)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until=wait_until, timeout=self.timeout * 1000)
            content = page.content()
            browser.close()

        return ScraperResponse(
            content=content.encode("utf-8"),
            content_type="text/html",
            encoding="utf-8",
            status_code=200,
            final_url=page.url,
        )

    async def _async_scrape_with_browser(self, url: str, options: ScraperOptions = None) -> ScraperResponse:
        from playwright.async_api import async_playwright

        wait_until = self._get_wait_until(options)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until=wait_until, timeout=self.timeout * 1000)
            content = await page.content()
            await browser.close()

        return ScraperResponse(
            content=content.encode("utf-8"),
            content_type="text/html",
            encoding="utf-8",
            status_code=200,
            final_url=page.url,
        )

    def _get_wait_until(self, options: ScraperOptions = None) -> str:
        if options is not None:
            return getattr(options, "wait_until", "load")
        return "load"

    @property
    def http_proxy(self) -> str:
        return self._http_proxy

    @http_proxy.setter
    def http_proxy(self, value: str):
        self._http_proxy = value

    @property
    def https_proxy(self) -> str:
        return self._https_proxy

    @https_proxy.setter
    def https_proxy(self, value: str):
        self._https_proxy = value

    @property
    def verify_ca(self) -> bool:
        return self._verify_ca

    @verify_ca.setter
    def verify_ca(self, value: bool):
        self._verify_ca = value
