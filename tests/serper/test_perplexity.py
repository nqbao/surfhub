import respx
import httpx
import pytest
from surfhub.serper.perplexity import PerplexitySearch
from surfhub.serper.model import SerpRequestOptions, TimeRange

PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"


def test_perplexity_basic():
    with respx.mock:
        respx.post(PERPLEXITY_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "resp_123",
                    "model": "sonar-pro",
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": "The answer to your query.",
                            }
                        }
                    ],
                    "citations": [
                        "https://example.com/article1",
                        "https://example.com/article2",
                    ],
                },
            )
        )

        serp = PerplexitySearch(api_key="test_key")
        resp = serp.serp("test query")
        assert len(resp.items) == 2
        assert resp.items[0].link == "https://example.com/article1"
        assert resp.items[1].link == "https://example.com/article2"
        assert resp.answer == "The answer to your query."


def test_perplexity_no_citations():
    with respx.mock:
        respx.post(PERPLEXITY_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "resp_123",
                    "model": "sonar-pro",
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": "No sources available.",
                            }
                        }
                    ],
                    "citations": [],
                },
            )
        )

        serp = PerplexitySearch(api_key="test_key")
        resp = serp.serp("test query")
        assert len(resp.items) == 0
        assert resp.answer == "No sources available."


def test_perplexity_params():
    serp = PerplexitySearch(api_key="test_key")

    params = serp.get_serp_params("test query")
    assert params["model"] == "sonar-pro"
    assert len(params["messages"]) == 2
    assert params["messages"][1]["content"] == "test query"


def test_perplexity_date_range():
    serp = PerplexitySearch(api_key="test_key")

    options = SerpRequestOptions(date_start="2025-01-01", date_end="2025-12-31")
    params = serp.get_serp_params("test query", options=options)
    content = params["messages"][1]["content"]
    assert "after 2025-01-01" in content
    assert "before 2025-12-31" in content


def test_perplexity_extra_options():
    serp = PerplexitySearch(api_key="test_key")

    options = SerpRequestOptions(extra_options={"temperature": 0.5, "model": "sonar"})
    params = serp.get_serp_params("test query", options=options)
    assert params["temperature"] == 0.5
    assert params["model"] == "sonar-pro"


def test_perplexity_headers():
    with respx.mock:
        route = respx.post(PERPLEXITY_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "answer"}}],
                    "citations": [],
                },
            )
        )

        serp = PerplexitySearch(api_key="test_api_key")
        serp.serp("test query")

        request = route.calls.last.request
        assert request.headers["Authorization"] == "Bearer test_api_key"
        assert request.headers["Content-Type"] == "application/json"


def test_perplexity_request_body():
    with respx.mock:
        route = respx.post(PERPLEXITY_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "answer"}}],
                    "citations": [],
                },
            )
        )

        serp = PerplexitySearch(api_key="test_key")
        serp.serp("test query")

        import json

        body = json.loads(route.calls.last.request.content)
        assert body["model"] == "sonar-pro"
        assert body["messages"][1]["content"] == "test query"


@pytest.mark.anyio
async def test_perplexity_async():
    with respx.mock:
        respx.post(PERPLEXITY_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "async answer"}}],
                    "citations": ["https://example.com"],
                },
            )
        )

        serp = PerplexitySearch(api_key="test_key")
        resp = await serp.async_serp("async query")
        assert len(resp.items) == 1
        assert resp.answer == "async answer"
