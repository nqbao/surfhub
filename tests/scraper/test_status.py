import httpx
import pytest
import respx

from surfhub.errors import InsufficientFundsError, ScrapingError
from surfhub.scraper.local import LocalScraper
from surfhub.scraper.scrapingbee import ScrapingBeeScraper
from surfhub.scraper.firecrawl import FirecrawlScraper


@pytest.mark.anyio
@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("status, attempts", [(201, 1), (404, 1), (429, 2), (503, 2)])
async def test_status_policy(asynchronous, local, status, attempts):
    scraper = LocalScraper() if local else ScrapingBeeScraper(api_key="test")
    scraper.retries = 2
    endpoint = "https://example.com" if local else scraper.api_url
    with respx.mock:
        route = respx.get(endpoint).respond(status, text="response body")
        if status == 201:
            result = (
                await scraper.async_scrape("https://example.com")
                if asynchronous
                else scraper.scrape("https://example.com")
            )
            assert result.status_code == status
        else:
            with pytest.raises(ScrapingError) as caught:
                if asynchronous:
                    await scraper.async_scrape("https://example.com")
                else:
                    scraper.scrape("https://example.com")
            assert caught.value.status_code == status
            assert caught.value.raw_body == "response body"
        assert route.call_count == attempts


@pytest.mark.anyio
@pytest.mark.parametrize("asynchronous", [False, True])
async def test_target_status_retries(asynchronous):
    scraper = FirecrawlScraper(api_key="test")
    with respx.mock:
        route = respx.post(scraper.api_url).mock(
            side_effect=[
                httpx.Response(
                    200, json={"data": {"markdown": "unavailable", "metadata": {"statusCode": 503}}}
                ),
                httpx.Response(200, json={"data": {"markdown": "ok", "metadata": {"statusCode": 200}}}),
            ]
        )
        result = (
            await scraper.async_scrape("https://example.com")
            if asynchronous
            else scraper.scrape("https://example.com")
        )
        assert result.content == b"ok"
        assert route.call_count == 2


def test_billing_does_not_retry():
    scraper = ScrapingBeeScraper(api_key="test")
    with respx.mock:
        route = respx.get(scraper.api_url).respond(429, text="quota exceeded")
        with pytest.raises(InsufficientFundsError):
            scraper.scrape("https://example.com")
        assert route.call_count == 1


@pytest.mark.parametrize("value", [0, -1, True, 1.5])
def test_invalid_retries(value):
    with pytest.raises(ValueError):
        LocalScraper().retries = value
