import respx
import httpx
import pytest
from surfhub.serper.jina import JinaSearch
from surfhub.serper.model import SerpRequestOptions

JINA_SEARCH_URL = "https://s.jina.ai"


def test_jina_search_basic():
    with respx.mock:
        respx.post(JINA_SEARCH_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "code": 200,
                    "status": 20000,
                    "data": [
                        {
                            "title": "Example Result",
                            "url": "https://example.com",
                            "description": "This is an example description",
                            "content": "Full content here...",
                            "usage": {"tokens": 500},
                        },
                        {
                            "title": "Another Result",
                            "url": "https://another.com",
                            "description": "Another description",
                            "content": "More content...",
                            "usage": {"tokens": 300},
                        },
                    ],
                },
            )
        )

        serp = JinaSearch(api_key="test_key")
        resp = serp.serp("test query")
        assert len(resp.items) == 2
        assert resp.items[0].title == "Example Result"
        assert resp.items[0].link == "https://example.com"
        assert resp.items[0].snippet == "This is an example description"
        assert resp.items[1].title == "Another Result"


def test_jina_search_empty_results():
    with respx.mock:
        respx.post(JINA_SEARCH_URL).mock(
            return_value=httpx.Response(
                200,
                json={"code": 200, "status": 20000, "data": []},
            )
        )

        serp = JinaSearch(api_key="test_key")
        resp = serp.serp("test query")
        assert len(resp.items) == 0


def test_jina_search_missing_data_field():
    with respx.mock:
        respx.post(JINA_SEARCH_URL).mock(
            return_value=httpx.Response(
                200,
                json={"code": 200, "status": 20000},
            )
        )

        serp = JinaSearch(api_key="test_key")
        resp = serp.serp("test query")
        assert len(resp.items) == 0


def test_jina_search_params():
    serp = JinaSearch(api_key="test_key")

    params = serp.get_serp_params("test query", num=10, page=1)
    assert params["q"] == "test query"
    assert params["num"] == 10
    assert params["page"] == 1


def test_jina_search_lang_country():
    serp = JinaSearch(api_key="test_key")

    options = SerpRequestOptions(lang="en", country="US", location="New York")
    params = serp.get_serp_params("test query", options=options)
    assert params["hl"] == "en"
    assert params["gl"] == "us"
    assert params["location"] == "New York"


def test_jina_search_date_range():
    serp = JinaSearch(api_key="test_key")

    options = SerpRequestOptions(date_start="2025-01-01", date_end="2025-12-31")
    params = serp.get_serp_params("test query", options=options)
    assert params["date_start"] == "2025-01-01"
    assert params["date_end"] == "2025-12-31"


def test_jina_search_extra_options():
    serp = JinaSearch(api_key="test_key")

    options = SerpRequestOptions(extra_options={"site": "example.com"})
    params = serp.get_serp_params("test query", options=options)
    assert params["site"] == "example.com"


def test_jina_search_headers():
    with respx.mock:
        route = respx.post(JINA_SEARCH_URL).mock(
            return_value=httpx.Response(
                200,
                json={"code": 200, "status": 20000, "data": []},
            )
        )

        serp = JinaSearch(api_key="test_api_key")
        serp.serp("test query")

        request = route.calls.last.request
        assert request.headers["Authorization"] == "Bearer test_api_key"
        assert request.headers["Content-Type"] == "application/json"
        assert request.headers["Accept"] == "application/json"


@pytest.mark.anyio
async def test_jina_search_async():
    with respx.mock:
        respx.post(JINA_SEARCH_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "code": 200,
                    "status": 20000,
                    "data": [
                        {
                            "title": "Async Result",
                            "url": "https://async.example.com",
                            "description": "Async description",
                            "content": "Async content",
                            "usage": {"tokens": 100},
                        }
                    ],
                },
            )
        )

        serp = JinaSearch(api_key="test_key")
        resp = await serp.async_serp("async query")
        assert len(resp.items) == 1
        assert resp.items[0].title == "Async Result"
