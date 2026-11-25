import abc
import re
from collections.abc import Callable
from typing import Self

import httpx
from pydantic import BaseModel, PrivateAttr
from surfhub.errors import (
    InsufficientFundsError,
    ResponseTooLargeError,
    ScrapingError,
    raise_for_insufficient_funds,
)

from ._body import ACCEPT_ENCODING, async_read_body, buffered_response, read_body

MarkdownEngine = Callable[[bytes], str | None]
_HTML_START = re.compile(rb"(?:<!doctype\s+html(?=[\s>])|<html(?=[\s/>]))", re.IGNORECASE)


class ScraperOptions(BaseModel):
    wait_until: str = "load"  # browser only: "load" | "domcontentloaded" | "networkidle"


class ScraperResponse(BaseModel):
    content: bytes
    content_type: str = ""
    encoding: str = "utf-8"
    final_url: str
    status_code: int
    _markdown_engine: MarkdownEngine | None = PrivateAttr(default=None)

    def _with_markdown_engine(self, engine: MarkdownEngine | None) -> Self:
        if self._markdown_engine is engine:
            return self
        response = self.model_copy()
        response._markdown_engine = engine
        return response

    def markdown(self, *, engine: MarkdownEngine | None = None) -> str:
        """Extract HTML as Markdown or decode an existing text response."""
        media_type = self.content_type.split(";", 1)[0].strip().lower()
        if not media_type:
            prefix = self.content[:1024].removeprefix(b"\xef\xbb\xbf").lstrip()
            if _HTML_START.match(prefix):
                media_type = "text/html"
        if media_type in ("text/html", "application/xhtml+xml"):
            if engine is None:
                engine = self._markdown_engine
            if engine is not None:
                result = engine(self.content)
                return result if result and result.strip() else ""

            import trafilatura

            for favor_recall in (False, True):
                result = trafilatura.extract(
                    self.content, output_format="markdown", include_tables=True, favor_recall=favor_recall
                )
                if result and result.strip():
                    return result
            return (trafilatura.html2txt(self.content) or "").strip()
        textual_application_types = ("application/json", "application/markdown", "application/x-markdown")
        if (
            media_type.startswith("text/")
            or media_type.endswith("+json")
            or media_type in textual_application_types
        ):
            return self.content.decode(self.encoding, errors="replace")
        return ""


class Scraper(abc.ABC):
    _retries: int = 3

    @property
    def retries(self) -> int:
        return self._retries

    @retries.setter
    def retries(self, value: int):
        if type(value) is not int or value < 1:
            raise ValueError("retries must be a positive integer")
        self._retries = value

    def validate_result(self, result: ScraperResponse) -> ScraperResponse:
        if not 200 <= result.status_code < 300:
            raise ScrapingError(
                f"Unexpected status code: {result.status_code}",
                status_code=result.status_code,
                raw_body=result.content.decode(result.encoding, errors="replace"),
            )
        return result

    def is_retriable_error(self, ex: Exception, resp: httpx.Response = None):
        if isinstance(ex, (ResponseTooLargeError, InsufficientFundsError)):
            return False
        if isinstance(ex, httpx.TransportError):
            return True
        status = getattr(ex, "status_code", None)
        if status is None and resp is not None:
            status = resp.status_code
        return status == 429 or (status is not None and 500 <= status < 600)

    _timeout: int = 30
    _max_bytes: int = 10 * 1024 * 1024
    _markdown_engine: MarkdownEngine | None = None

    def __init__(self, *, markdown_engine: MarkdownEngine | None = None):
        self._markdown_engine = markdown_engine

    @property
    def markdown_engine(self) -> MarkdownEngine | None:
        return self._markdown_engine

    @abc.abstractmethod
    def scrape(self, url: str, options: ScraperOptions = None, use_browser: bool = False) -> ScraperResponse:
        pass

    @abc.abstractmethod
    async def async_scrape(
        self, url: str, options: ScraperOptions = None, use_browser: bool = False
    ) -> ScraperResponse:
        pass

    @property
    def timeout(self) -> int:
        """
        Timeout in seconds for the HTTP request
        """
        return self._timeout

    @timeout.setter
    def timeout(self, value: int):
        self._timeout = value

    @property
    def max_bytes(self) -> int:
        return self._max_bytes

    @max_bytes.setter
    def max_bytes(self, value: int):
        if type(value) is not int or value <= 0:
            raise ValueError("max_bytes must be a positive integer")
        self._max_bytes = value


class BaseScraper(Scraper):
    default_api_url = ""
    _api_key: str = None
    _api_url: str = None
    _retries: int = 3

    def __init__(self, api_key: str = None, *, markdown_engine: MarkdownEngine | None = None):
        super().__init__(markdown_engine=markdown_engine)
        self._api_key = api_key

    def scrape(self, url, options: ScraperOptions = None, use_browser: bool = False) -> ScraperResponse:
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            for i in range(self.retries):
                resp = None
                try:
                    request = self.prepare_request(url, options, use_browser)
                    request.headers["Accept-Encoding"] = ACCEPT_ENCODING
                    resp = client.send(request, auth=self.get_request_auth(), stream=True)
                    try:
                        body = read_body(resp, self.max_bytes)
                    finally:
                        resp.close()
                    resp = buffered_response(resp, body)
                    self.validate_response(resp)
                    result = self.validate_result(self.parse_response(url, resp))
                except Exception as e:
                    if i < self.retries - 1 and self.is_retriable_error(e, resp):
                        continue

                    raise e

                break

        return result._with_markdown_engine(self.markdown_engine)

    async def async_scrape(
        self, url: str, options: ScraperOptions = None, use_browser: bool = False
    ) -> ScraperResponse:
        """
        Scrapes the content of a given URL asynchronously and returns it content
        """
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            for i in range(self.retries):
                resp = None
                try:
                    request = self.prepare_request(url, options, use_browser)
                    request.headers["Accept-Encoding"] = ACCEPT_ENCODING
                    resp = await client.send(request, auth=self.get_request_auth(), stream=True)
                    try:
                        body = await async_read_body(resp, self.max_bytes)
                    finally:
                        await resp.aclose()
                    resp = buffered_response(resp, body)
                    self.validate_response(resp)
                    result = self.validate_result(self.parse_response(url, resp))
                except Exception as e:
                    if i < self.retries - 1 and self.is_retriable_error(e, resp):
                        continue

                    raise e

                break

        return result._with_markdown_engine(self.markdown_engine)

    @abc.abstractmethod
    def prepare_request(
        self, url: str, options: ScraperOptions = None, use_browser: bool = False
    ) -> httpx.Request:
        pass

    @abc.abstractmethod
    def parse_response(self, url: str, resp: httpx.Response) -> ScraperResponse:
        pass

    def get_request_auth(self):
        return None

    def validate_response(self, resp: httpx.Response):
        if not 200 <= resp.status_code < 300:
            raise_for_insufficient_funds(resp)
            raise ScrapingError(
                "Unexpected status code: " + str(resp.status_code),
                status_code=resp.status_code,
                raw_body=resp.text,
            )

    @property
    def api_key(self) -> str:
        return self._api_key

    @api_key.setter
    def api_key(self, value: str):
        self._api_key = value

    @property
    def api_url(self) -> str:
        return self._api_url or self.default_api_url

    @api_url.setter
    def api_url(self, value: str):
        self._api_url = value
