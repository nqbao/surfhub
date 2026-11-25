import httpx

from surfhub.errors import ScrapingError

from ._public_http import PublicAsyncHTTPTransport, PublicHTTPTransport
from .model import Scraper, ScraperOptions, ScraperResponse


class LocalScraper(Scraper):
    """Scrape public HTTP(S) URLs. Enable trusted mode for browsers or private networks."""

    _http_proxy: str = ""
    _https_proxy: str = ""
    _verify_ca: bool = True

    def __init__(self, *, allow_private_network: bool = False):
        self._allow_private_network = allow_private_network

    @property
    def allow_private_network(self) -> bool:
        return self._allow_private_network

    def _client_options(self, transport_type, public_transport_type):
        options = {"timeout": self.timeout, "follow_redirects": True}
        if self.allow_private_network:
            options["verify"] = self.verify_ca
            options["mounts"] = {
                scheme: transport_type(proxy=proxy, verify=self.verify_ca)
                for scheme, proxy in (("http://", self.http_proxy), ("https://", self.https_proxy))
                if proxy
            }
        else:
            if self.http_proxy or self.https_proxy:
                raise ScrapingError("A local proxy requires allow_private_network=True")
            options["transport"] = public_transport_type(verify=self.verify_ca)
            options["trust_env"] = False
        return options

    def _check_browser_allowed(self):
        if not self.allow_private_network:
            raise ScrapingError("Local browser mode requires allow_private_network=True and trusted content")

    def scrape(self, url: str, options: ScraperOptions = None, use_browser: bool = False) -> ScraperResponse:
        if use_browser:
            self._check_browser_allowed()
            return self._scrape_with_browser(url, options)

        options = self._client_options(httpx.HTTPTransport, PublicHTTPTransport)
        with httpx.Client(**options) as client:
            return self._http_response(client.get(url))

    async def async_scrape(
        self, url: str, options: ScraperOptions = None, use_browser: bool = False
    ) -> ScraperResponse:
        if use_browser:
            self._check_browser_allowed()
            return await self._async_scrape_with_browser(url, options)

        options = self._client_options(httpx.AsyncHTTPTransport, PublicAsyncHTTPTransport)
        async with httpx.AsyncClient(**options) as client:
            return self._http_response(await client.get(url))

    @staticmethod
    def _http_response(resp: httpx.Response) -> ScraperResponse:
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
