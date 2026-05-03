import pytest
import respx
import httpx
from surfhub.errors import (
    InsufficientFundsError,
    is_insufficient_funds,
    check_insufficient_funds,
    ScrapingError,
)
from surfhub.scraper import ZyteScraper
from surfhub.serper.brave import BraveSearch
from surfhub.serper.serpapi import SerpApi as SerpApiProvider
from surfhub.serper.serper import SerperDev
from surfhub.serper.google import GoogleCustomSearch
from surfhub.serper.valueserp import ValueSerp


class TestIsInsufficientFunds:
    def test_status_402_always_true(self):
        assert is_insufficient_funds(402, "") is True
        assert is_insufficient_funds(402, "any body") is True

    def test_status_403_with_keywords(self):
        assert is_insufficient_funds(403, "insufficient balance") is True
        assert is_insufficient_funds(403, "Quota Exceeded") is True
        assert is_insufficient_funds(403, "exceeded your quota") is True
        assert is_insufficient_funds(403, "out of credits") is True
        assert is_insufficient_funds(403, "no credits remaining") is True
        assert is_insufficient_funds(403, "quota limit reached") is True
        assert is_insufficient_funds(403, "payment required") is True
        assert is_insufficient_funds(403, "billing issue") is True
        assert is_insufficient_funds(403, "low balance") is True

    def test_status_403_without_keywords(self):
        assert is_insufficient_funds(403, "access denied") is False
        assert is_insufficient_funds(403, "forbidden") is False
        assert is_insufficient_funds(403, "") is False

    def test_status_429_with_keywords(self):
        assert is_insufficient_funds(429, "quota exceeded") is True
        assert is_insufficient_funds(429, "insufficient credits") is True

    def test_status_429_without_keywords(self):
        assert is_insufficient_funds(429, "rate limited") is False
        assert is_insufficient_funds(429, "too many requests") is False

    def test_other_status_codes(self):
        assert is_insufficient_funds(200, "insufficient balance") is False
        assert is_insufficient_funds(500, "insufficient balance") is False
        assert is_insufficient_funds(404, "quota exceeded") is False


class TestCheckInsufficientFunds:
    def test_raises_with_keyword(self):
        with pytest.raises(InsufficientFundsError) as exc:
            check_insufficient_funds("insufficient balance", status_code=403)
        assert exc.value.status_code == 403

    def test_raises_with_quota_keyword(self):
        with pytest.raises(InsufficientFundsError):
            check_insufficient_funds("quota exceeded for this month")

    def test_does_not_raise_without_keyword(self):
        check_insufficient_funds("invalid api key")

    def test_does_not_raise_with_regular_error(self):
        check_insufficient_funds("something went wrong")


class TestScraperInsufficientFunds:
    def test_402_raises_insufficient_funds(self):
        with respx.mock:
            respx.post("https://api.zyte.com/v1/extract").mock(
                return_value=httpx.Response(402, text="payment required")
            )
            scraper = ZyteScraper(api_key="test_key")
            with pytest.raises(InsufficientFundsError) as exc:
                scraper.scrape("http://example.com")
            assert exc.value.status_code == 402

    def test_403_quota_exceeded_raises_insufficient_funds(self):
        with respx.mock:
            respx.post("https://api.zyte.com/v1/extract").mock(
                return_value=httpx.Response(403, text="quota exceeded")
            )
            scraper = ZyteScraper(api_key="test_key")
            with pytest.raises(InsufficientFundsError):
                scraper.scrape("http://example.com")

    def test_403_forbidden_still_raises_scraping_error(self):
        with respx.mock:
            respx.post("https://api.zyte.com/v1/extract").mock(
                return_value=httpx.Response(403, text="forbidden")
            )
            scraper = ZyteScraper(api_key="test_key")
            with pytest.raises(ScrapingError):
                scraper.scrape("http://example.com")

    def test_429_quota_raises_insufficient_funds(self):
        with respx.mock:
            respx.post("https://api.zyte.com/v1/extract").mock(
                return_value=httpx.Response(429, text="exceeded your quota")
            )
            scraper = ZyteScraper(api_key="test_key")
            with pytest.raises(InsufficientFundsError):
                scraper.scrape("http://example.com")

    def test_429_rate_limit_still_raises_scraping_error(self):
        with respx.mock:
            respx.post("https://api.zyte.com/v1/extract").mock(
                return_value=httpx.Response(429, text="too many requests")
            )
            scraper = ZyteScraper(api_key="test_key")
            with pytest.raises(ScrapingError):
                scraper.scrape("http://example.com")


class TestSerperBaseInsufficientFunds:
    def test_http_402_raises_insufficient_funds(self):
        with respx.mock:
            respx.get("https://api.search.brave.com/res/v1/web/search").mock(
                return_value=httpx.Response(402, text="payment required")
            )
            serp = BraveSearch(api_key="test_key")
            with pytest.raises(InsufficientFundsError) as exc:
                serp.serp("test query")
            assert exc.value.status_code == 402

    def test_http_403_quota_raises_insufficient_funds(self):
        with respx.mock:
            respx.get("https://api.search.brave.com/res/v1/web/search").mock(
                return_value=httpx.Response(403, text="insufficient balance")
            )
            serp = BraveSearch(api_key="test_key")
            with pytest.raises(InsufficientFundsError):
                serp.serp("test query")

    def test_http_403_forbidden_still_raises_http_error(self):
        with respx.mock:
            respx.get("https://api.search.brave.com/res/v1/web/search").mock(
                return_value=httpx.Response(403, text="forbidden")
            )
            serp = BraveSearch(api_key="test_key")
            with pytest.raises(httpx.HTTPStatusError):
                serp.serp("test query")


class TestSerpApiProviderInsufficientFunds:
    def test_json_error_insufficient_balance(self):
        with respx.mock:
            respx.get("https://serpapi.com/search").mock(
                return_value=httpx.Response(200, json={"error": "insufficient balance"})
            )
            serp = SerpApiProvider(api_key="test_key")
            with pytest.raises(InsufficientFundsError):
                serp.serp("test query")

    def test_json_error_regular_error(self):
        with respx.mock:
            respx.get("https://serpapi.com/search").mock(
                return_value=httpx.Response(200, json={"error": "invalid api key"})
            )
            serp = SerpApiProvider(api_key="test_key")
            from surfhub.errors import SerpApiError
            with pytest.raises(SerpApiError, match="invalid api key"):
                serp.serp("test query")


class TestSerperDevInsufficientFunds:
    def test_status_code_error_quota_exceeded(self):
        with respx.mock:
            respx.get("https://google.serper.dev/search").mock(
                return_value=httpx.Response(
                    200, json={"statusCode": 429, "message": "quota exceeded"}
                )
            )
            serp = SerperDev(api_key="test_key")
            with pytest.raises(InsufficientFundsError):
                serp.serp("test query")

    def test_status_code_error_regular(self):
        with respx.mock:
            respx.get("https://google.serper.dev/search").mock(
                return_value=httpx.Response(
                    200, json={"statusCode": 400, "message": "bad request"}
                )
            )
            serp = SerperDev(api_key="test_key")
            from surfhub.errors import SerpApiError
            with pytest.raises(SerpApiError, match="bad request"):
                serp.serp("test query")


class TestGoogleCustomSearchInsufficientFunds:
    def test_error_quota_exceeded(self):
        with respx.mock:
            respx.get("https://www.googleapis.com/customsearch/v1").mock(
                return_value=httpx.Response(
                    200, json={"error": {"message": "exceeded your quota"}}
                )
            )
            serp = GoogleCustomSearch(api_key="cx:key")
            with pytest.raises(InsufficientFundsError):
                serp.serp("test query")

    def test_error_regular(self):
        with respx.mock:
            respx.get("https://www.googleapis.com/customsearch/v1").mock(
                return_value=httpx.Response(
                    200, json={"error": {"message": "invalid api key"}}
                )
            )
            serp = GoogleCustomSearch(api_key="cx:key")
            from surfhub.errors import SerpApiError
            with pytest.raises(SerpApiError, match="invalid api key"):
                serp.serp("test query")


class TestValueSerpInsufficientFunds:
    def test_request_info_failure_insufficient_balance(self):
        with respx.mock:
            respx.get("https://api.valueserp.com/search").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "request_info": {
                            "success": False,
                            "message": "insufficient balance to complete request",
                        }
                    },
                )
            )
            serp = ValueSerp(api_key="test_key")
            with pytest.raises(InsufficientFundsError):
                serp.serp("test query")

    def test_request_info_failure_regular(self):
        with respx.mock:
            respx.get("https://api.valueserp.com/search").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "request_info": {
                            "success": False,
                            "message": "invalid api key",
                        }
                    },
                )
            )
            serp = ValueSerp(api_key="test_key")
            from surfhub.errors import SerpApiError
            with pytest.raises(SerpApiError, match="invalid api key"):
                serp.serp("test query")
