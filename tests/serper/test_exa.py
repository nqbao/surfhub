import respx
import httpx
import pytest
from surfhub.serper.exa import ExaSearch
from surfhub.serper.model import SerpRequestOptions, TimeRange

EXA_URL = "https://api.exa.ai/search"


def test_exa_basic():
    with respx.mock:
        respx.post(EXA_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "title": "Example Result",
                            "url": "https://example.com",
                            "text": "Some page content",
                        }
                    ]
                },
            )
        )
        serp = ExaSearch(api_key="test_key")
        resp = serp.serp("test query")
        assert len(resp.items) == 1
        assert resp.items[0].title == "Example Result"
        assert resp.items[0].link == "https://example.com"
        assert resp.items[0].snippet == "Some page content"


def test_exa_auth_header():
    with respx.mock:
        route = respx.post(EXA_URL).mock(
            return_value=httpx.Response(200, json={"results": []})
        )
        serp = ExaSearch(api_key="my_secret_key")
        serp.serp("query")
        assert route.calls[0].request.headers["x-api-key"] == "my_secret_key"


def test_exa_num_results():
    serp = ExaSearch(api_key="test_key")
    params = serp.get_serp_params("query", num=5)
    assert params["numResults"] == 5


def test_exa_date_start():
    serp = ExaSearch(api_key="test_key")
    options = SerpRequestOptions(date_start="2024-01-01")
    params = serp.get_serp_params("query", options=options)
    assert params["startPublishedDate"] == "2024-01-01T00:00:00.000Z"
    assert "endPublishedDate" not in params


def test_exa_date_end():
    serp = ExaSearch(api_key="test_key")
    options = SerpRequestOptions(date_end="2024-12-31")
    params = serp.get_serp_params("query", options=options)
    assert params["endPublishedDate"] == "2024-12-31T23:59:59.999Z"
    assert "startPublishedDate" not in params


def test_exa_date_range():
    serp = ExaSearch(api_key="test_key")
    options = SerpRequestOptions(date_start="2024-01-01", date_end="2024-12-31")
    params = serp.get_serp_params("query", options=options)
    assert params["startPublishedDate"] == "2024-01-01T00:00:00.000Z"
    assert params["endPublishedDate"] == "2024-12-31T23:59:59.999Z"


def test_exa_extra_options():
    serp = ExaSearch(api_key="test_key")
    options = SerpRequestOptions(extra_options={"type": "neural", "includeDomains": ["example.com"]})
    params = serp.get_serp_params("query", options=options)
    assert params["type"] == "neural"
    assert params["includeDomains"] == ["example.com"]


def test_exa_default_type():
    serp = ExaSearch(api_key="test_key")
    params = serp.get_serp_params("query")
    assert params["type"] == "auto"


def test_exa_empty_results():
    with respx.mock:
        respx.post(EXA_URL).mock(
            return_value=httpx.Response(200, json={"results": []})
        )
        serp = ExaSearch(api_key="test_key")
        resp = serp.serp("query")
        assert resp.items == []


@pytest.mark.anyio
async def test_exa_async():
    with respx.mock:
        respx.post(EXA_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"title": "Async Result", "url": "https://async.example.com", "text": "content"}
                    ]
                },
            )
        )
        serp = ExaSearch(api_key="test_key")
        resp = await serp.async_serp("async query")
        assert len(resp.items) == 1
        assert resp.items[0].title == "Async Result"
