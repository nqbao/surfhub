import respx
import httpx
from surfhub.serper.brave import BraveSearch
from surfhub.serper.model import SerpRequestOptions, TimeRange


def test_brave_basic():
    """Test basic Brave Search"""
    with respx.mock:
        respx.get("https://api.search.brave.com/res/v1/web/search").mock(
            return_value=httpx.Response(
                200,
                json={
                    "type": "search",
                    "web": {
                        "type": "search",
                        "results": [
                            {
                                "title": "Example Result",
                                "url": "https://example.com",
                                "description": "This is an example content",
                                "type": "search_result",
                            }
                        ],
                    },
                },
            )
        )

        serp = BraveSearch(api_key="test_key")
        resp = serp.serp("test query")
        assert len(resp.items) == 1
        assert resp.items[0].title == "Example Result"
        assert resp.items[0].link == "https://example.com"
        assert resp.items[0].snippet == "This is an example content"


def test_brave_web_and_news():
    """Test Brave Search with both web and news results"""
    with respx.mock:
        respx.get("https://api.search.brave.com/res/v1/web/search").mock(
            return_value=httpx.Response(
                200,
                json={
                    "type": "search",
                    "web": {
                        "type": "search",
                        "results": [
                            {"title": "Web Result", "url": "https://example.com", "description": "Web content"}
                        ],
                    },
                    "news": {
                        "type": "news",
                        "results": [
                            {
                                "title": "Breaking News",
                                "url": "https://news.com/article",
                                "description": "News summary",
                                "breaking": True,
                            }
                        ],
                    },
                },
            )
        )

        serp = BraveSearch(api_key="test_key")
        resp = serp.serp("test query")
        assert len(resp.items) == 2
        assert resp.items[0].title == "Web Result"
        assert resp.items[0].prefix == ""
        assert resp.items[1].title == "Breaking News"
        assert resp.items[1].prefix == "[News]"


def test_brave_params():
    """Test parameter mapping"""
    serp = BraveSearch(api_key="test_key")

    # Test num parameter
    params = serp.get_serp_params("test query", num=20)
    assert params["count"] == 20

    # Test offset parameter
    params = serp.get_serp_params("test query", page=2)
    assert params["offset"] == 2

    # Test country parameter (should be uppercase)
    options = SerpRequestOptions(country="us")
    params = serp.get_serp_params("test query", options=options)
    assert params["country"] == "US"

    # Test language parameter
    options = SerpRequestOptions(lang="en")
    params = serp.get_serp_params("test query", options=options)
    assert params["search_lang"] == "en"

    # Test extra options
    options = SerpRequestOptions(extra_options={"safesearch": "strict"})
    params = serp.get_serp_params("test query", options=options)
    assert params["safesearch"] == "strict"


def test_brave_time_filtering():
    """Test time filtering with freshness parameter"""
    serp = BraveSearch(api_key="test_key")

    # Test TimeRange mapping
    options = SerpRequestOptions(time_range=TimeRange.DAY)
    params = serp.get_serp_params("test query", options=options)
    assert params["freshness"] == "pd"  # past day

    options = SerpRequestOptions(time_range=TimeRange.WEEK)
    params = serp.get_serp_params("test query", options=options)
    assert params["freshness"] == "pw"  # past week

    options = SerpRequestOptions(time_range=TimeRange.MONTH)
    params = serp.get_serp_params("test query", options=options)
    assert params["freshness"] == "pm"  # past month

    options = SerpRequestOptions(time_range=TimeRange.YEAR)
    params = serp.get_serp_params("test query", options=options)
    assert params["freshness"] == "py"  # past year

    # Test custom date range
    options = SerpRequestOptions(date_start="2025-01-01", date_end="2025-12-31")
    params = serp.get_serp_params("test query", options=options)
    assert params["freshness"] == "2025-01-01to2025-12-31"


def test_brave_empty_results():
    """Test handling of empty results"""
    with respx.mock:
        respx.get("https://api.search.brave.com/res/v1/web/search").mock(
            return_value=httpx.Response(200, json={"type": "search", "query": {"original": "test query"}})
        )

        serp = BraveSearch(api_key="test_key")
        resp = serp.serp("test query")
        assert len(resp.items) == 0


def test_brave_headers():
    """Test that proper headers are sent"""
    with respx.mock:
        route = respx.get("https://api.search.brave.com/res/v1/web/search").mock(
            return_value=httpx.Response(200, json={"type": "search", "web": {"results": []}})
        )

        serp = BraveSearch(api_key="test_api_key")
        serp.serp("test query")

        # Verify headers were sent
        request = route.calls.last.request
        assert request.headers["X-Subscription-Token"] == "test_api_key"
        assert request.headers["Accept"] == "application/json"
        assert request.headers["Accept-Encoding"] == "gzip"
