import httpx

from surfhub._version import __version__
from surfhub.errors import ScrapingError

from ._body import ACCEPT_ENCODING, async_read_body, check_size, read_body
from ._public_http import PublicAsyncHTTPTransport, PublicHTTPTransport
from .model import MarkdownEngine, Scraper, ScraperOptions, ScraperResponse


DEFAULT_USER_AGENT = f"surfhub/{__version__} (https://github.com/nqbao/surfhub)"


class LocalScraper(Scraper):
    """Scrape public HTTP(S) URLs. Enable trusted mode for browsers or private networks."""

    _http_proxy: str = ""
    _https_proxy: str = ""
    _verify_ca: bool = True

    def __init__(
        self,
        *,
        allow_private_network: bool = False,
        user_agent: str = DEFAULT_USER_AGENT,
        markdown_engine: MarkdownEngine | None = None,
    ):
        super().__init__(markdown_engine=markdown_engine)
        self._allow_private_network = allow_private_network
        self._user_agent = user_agent

    @property
    def allow_private_network(self) -> bool:
        return self._allow_private_network

    @property
    def user_agent(self) -> str:
        return self._user_agent

    def _client_options(self, transport_type, public_transport_type):
        options = {
            "timeout": self.timeout,
            "headers": {"User-Agent": self.user_agent, "Accept-Encoding": ACCEPT_ENCODING},
        }
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
        for attempt in range(self.retries):
            try:
                return self.validate_result(self._scrape_once(url, options, use_browser))
            except Exception as error:
                if attempt == self.retries - 1 or not self.is_retriable_error(error):
                    raise

    def _scrape_once(self, url: str, options: ScraperOptions = None, use_browser: bool = False) -> ScraperResponse:
        if use_browser:
            self._check_browser_allowed()
            return self._scrape_with_browser(url, options)

        options = self._client_options(httpx.HTTPTransport, PublicHTTPTransport)
        with httpx.Client(**options) as client:
            request = client.build_request("GET", url)
            for _ in range(client.max_redirects + 1):
                resp = client.send(request, stream=True)
                try:
                    if resp.next_request is None:
                        return self._http_response(resp, read_body(resp, self.max_bytes))
                    request = resp.next_request
                finally:
                    resp.close()
            raise httpx.TooManyRedirects("Exceeded maximum allowed redirects.", request=request)

    async def async_scrape(
        self, url: str, options: ScraperOptions = None, use_browser: bool = False
    ) -> ScraperResponse:
        for attempt in range(self.retries):
            try:
                return self.validate_result(await self._async_scrape_once(url, options, use_browser))
            except Exception as error:
                if attempt == self.retries - 1 or not self.is_retriable_error(error):
                    raise

    async def _async_scrape_once(
        self, url: str, options: ScraperOptions = None, use_browser: bool = False
    ) -> ScraperResponse:
        if use_browser:
            self._check_browser_allowed()
            return await self._async_scrape_with_browser(url, options)

        options = self._client_options(httpx.AsyncHTTPTransport, PublicAsyncHTTPTransport)
        async with httpx.AsyncClient(**options) as client:
            request = client.build_request("GET", url)
            for _ in range(client.max_redirects + 1):
                resp = await client.send(request, stream=True)
                try:
                    if resp.next_request is None:
                        return self._http_response(resp, await async_read_body(resp, self.max_bytes))
                    request = resp.next_request
                finally:
                    await resp.aclose()
            raise httpx.TooManyRedirects("Exceeded maximum allowed redirects.", request=request)

    def _http_response(self, resp: httpx.Response, content: bytes) -> ScraperResponse:
        response = ScraperResponse(
            content=content,
            content_type=resp.headers.get("content-type", ""),
            encoding=resp.encoding or "utf-8",
            status_code=resp.status_code,
            final_url=str(resp.url),
        )
        return response._with_markdown_engine(self.markdown_engine)

    def _scrape_with_browser(self, url: str, options: ScraperOptions = None) -> ScraperResponse:
        from playwright.sync_api import sync_playwright

        wait_until = self._get_wait_until(options)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            navigation = page.goto(url, wait_until=wait_until, timeout=self.timeout * 1000)
            content = page.content()
            browser.close()

        return self._browser_response(content, page.url, navigation.status if navigation else 200)

    async def _async_scrape_with_browser(self, url: str, options: ScraperOptions = None) -> ScraperResponse:
        from playwright.async_api import async_playwright

        wait_until = self._get_wait_until(options)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            navigation = await page.goto(url, wait_until=wait_until, timeout=self.timeout * 1000)
            content = await page.content()
            await browser.close()

        return self._browser_response(content, page.url, navigation.status if navigation else 200)

    def _browser_response(self, content: str, url: str, status_code: int) -> ScraperResponse:
        check_size(len(content), self.max_bytes)
        encoded = content.encode("utf-8")
        check_size(len(encoded), self.max_bytes)
        response = ScraperResponse(
            content=encoded,
            content_type="text/html",
            encoding="utf-8",
            status_code=status_code,
            final_url=url,
        )
        return response._with_markdown_engine(self.markdown_engine)

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
