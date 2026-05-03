import pytest
import respx
import httpx
from surfhub.errors import (
    InsufficientFundsError,
    is_insufficient_funds,
    check_insufficient_funds,
    ScrapingError,
    SerpApiError,
)
from surfhub.scraper import ZyteScraper
from surfhub.scraper.firecrawl import FirecrawlScraper
from surfhub.serper.brave import BraveSearch
from surfhub.serper.serpapi import SerpApi as SerpApiProvider
from surfhub.serper.serper import SerperDev
from surfhub.serper.google import GoogleCustomSearch
from surfhub.serper.valueserp import ValueSerp
from surfhub.serper.perplexity import PerplexitySearch
from surfhub.serper.exa import ExaSearch
from surfhub.serper.jina import JinaSearch
from surfhub.serper.tavily import Tavily


class TestIsInsufficientFunds:
    def test_status_402_always_true(self):
        assert is_insufficient_funds(402, "") is True
        assert is_insufficient_funds(402, "any body") is True

    def test_status_403_with_keywords(self):
        assert is_insufficient_funds(403, "insufficient balance") is True
        assert is_insufficient_funds(403, "Quota Exceeded") is True
        assert is_insufficient_funds(403, "exceeded your quota") is True
        assert is_insufficient_funds(403, "out of credits") is True
        assert is_insufficient_funds(403, "no_more_credits") is True
        assert is_insufficient_funds(403, "quota limit reached") is True
        assert is_insufficient_funds(403, "payment required") is True
        assert is_insufficient_funds(403, "billing error") is True
        # real API patterns
        assert is_insufficient_funds(403, "daily limit exceeded") is True
        assert is_insufficient_funds(403, "dailyLimitExceeded") is True
        assert is_insufficient_funds(403, "account suspended") is True
        assert is_insufficient_funds(403, "InsufficientBalanceError") is True
        assert is_insufficient_funds(403, "please recharge") is True
        assert is_insufficient_funds(403, "budget exceeded") is True

    def test_status_403_without_keywords(self):
        assert is_insufficient_funds(403, "access denied") is False
        assert is_insufficient_funds(403, "forbidden") is False
        assert is_insufficient_funds(403, "") is False

    def test_status_429_with_keywords(self):
        assert is_insufficient_funds(429, "quota exceeded") is True
        assert is_insufficient_funds(429, "insufficient credits") is True
        # SerpApi real error: 429 + "Your account has run out of searches"
        assert is_insufficient_funds(429, "Your account has run out of searches") is True
        assert is_insufficient_funds(429, "run out of credits") is True
        assert is_insufficient_funds(429, "credits exhausted") is True
        assert is_insufficient_funds(429, "no_more_credits") is True

    def test_status_429_without_keywords(self):
        assert is_insufficient_funds(429, "rate limited") is False
        assert is_insufficient_funds(429, "too many requests") is False
        # regular Brave Search rate limit (no body keywords)
        assert is_insufficient_funds(429, "") is False

    def test_status_432_plan_limit(self):
        # Tavily uses 432 for plan limit exceeded
        assert is_insufficient_funds(432, "plan limit exceeded") is True
        assert is_insufficient_funds(432, "quota exceeded for plan") is True
        # 432 only triggers with keywords
        assert is_insufficient_funds(432, "") is False

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

    @pytest.mark.anyio
    async def test_async_402_raises_insufficient_funds(self):
        with respx.mock:
            respx.get("https://api.search.brave.com/res/v1/web/search").mock(
                return_value=httpx.Response(402, text="payment required")
            )
            serp = BraveSearch(api_key="test_key")
            with pytest.raises(InsufficientFundsError) as exc:
                await serp.async_serp("test query")
            assert exc.value.status_code == 402


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
            with pytest.raises(SerpApiError, match="invalid api key"):
                serp.serp("test query")


class TestRealApiPatterns:
    """Tests matching actual error responses from live API providers."""

    def test_serpapi_run_out_of_searches(self):
        # SerpApi returns 200 + {"error": "Your account has run out of searches."}
        # but also 429 at HTTP level when exhausted
        with respx.mock:
            respx.get("https://serpapi.com/search").mock(
                return_value=httpx.Response(200, json={"error": "Your account has run out of searches."})
            )
            serp = SerpApiProvider(api_key="test_key")
            with pytest.raises(InsufficientFundsError):
                serp.serp("test query")

    def test_google_daily_limit_exceeded(self):
        # Google CSE: 200 + {"error": {"message": "Request throttled due to daily limit being reached."}}
        with respx.mock:
            respx.get("https://www.googleapis.com/customsearch/v1").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "error": {
                            "code": 403,
                            "message": "Request throttled due to daily limit being reached.",
                            "errors": [{"reason": "dailyLimitExceeded"}],
                        }
                    },
                )
            )
            serp = GoogleCustomSearch(api_key="cx:key")
            with pytest.raises(InsufficientFundsError):
                serp.serp("test query")

    def test_perplexity_402(self):
        # Perplexity: 402 + {"error": {"message": "Insufficient credits", "type": "billing_error"}}
        with respx.mock:
            respx.post("https://api.perplexity.ai/chat/completions").mock(
                return_value=httpx.Response(
                    402,
                    json={"error": {"message": "Insufficient credits", "type": "billing_error"}},
                )
            )
            serp = PerplexitySearch(api_key="test_key")
            with pytest.raises(InsufficientFundsError):
                serp.serp("test query")

    def test_firecrawl_402(self):
        # Firecrawl: 402 + {"success": false, "error": "Payment required to access this resource."}
        with respx.mock:
            respx.post("https://api.firecrawl.dev/v1/scrape").mock(
                return_value=httpx.Response(
                    402,
                    json={"success": False, "error": "Payment required to access this resource."},
                )
            )
            scraper = FirecrawlScraper(api_key="test_key")
            with pytest.raises(InsufficientFundsError):
                scraper.scrape("http://example.com")

    def test_exa_402_no_more_credits(self):
        # ExaSearch: 402 + {"tag": "NO_MORE_CREDITS", "error": "..."}
        with respx.mock:
            respx.post("https://api.exa.ai/search").mock(
                return_value=httpx.Response(
                    402,
                    json={"requestId": "abc123", "error": "Account credits exhausted", "tag": "NO_MORE_CREDITS"},
                )
            )
            serp = ExaSearch(api_key="test_key")
            with pytest.raises(InsufficientFundsError):
                serp.serp("test query")

    def test_jina_insufficient_balance(self):
        # Jina: 402 + {"name": "InsufficientBalanceError", "message": "Account balance not enough"}
        with respx.mock:
            respx.post("https://s.jina.ai").mock(
                return_value=httpx.Response(
                    402,
                    json={
                        "data": None,
                        "code": 402,
                        "name": "InsufficientBalanceError",
                        "status": 40203,
                        "message": "Account balance not enough to run this query, please recharge.",
                        "readableMessage": "InsufficientBalanceError: Account balance not enough",
                    },
                )
            )
            serp = JinaSearch(api_key="test_key")
            with pytest.raises(InsufficientFundsError):
                serp.serp("test query")

    def test_tavily_432_plan_limit(self):
        # Tavily: HTTP 432 Plan Limit Exceeded
        with respx.mock:
            respx.post("https://api.tavily.com/search").mock(
                return_value=httpx.Response(
                    432,
                    json={"error": "plan limit exceeded"},
                )
            )
            serp = Tavily(api_key="test_key")
            with pytest.raises(InsufficientFundsError):
                serp.serp("test query")

    def test_exa_402_budget_exceeded(self):
        # ExaSearch: 402 + {"tag": "API_KEY_BUDGET_EXCEEDED"}
        with respx.mock:
            respx.post("https://api.exa.ai/search").mock(
                return_value=httpx.Response(
                    402,
                    json={"requestId": "xyz789", "error": "Key budget exceeded", "tag": "API_KEY_BUDGET_EXCEEDED"},
                )
            )
            serp = ExaSearch(api_key="test_key")
            with pytest.raises(InsufficientFundsError):
                serp.serp("test query")

    def test_zyte_account_suspended(self):
        # Zyte: 403 + {"status": 403, "type": "/auth/account-suspended"}
        with respx.mock:
            respx.post("https://api.zyte.com/v1/extract").mock(
                return_value=httpx.Response(
                    403,
                    json={"status": 403, "type": "/auth/account-suspended"},
                )
            )
            scraper = ZyteScraper(api_key="test_key")
            with pytest.raises(InsufficientFundsError):
                scraper.scrape("http://example.com")
