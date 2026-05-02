import respx
import httpx
from surfhub.serper.tavily import Tavily
from surfhub.serper.model import SerpRequestOptions, TimeRange


def test_tavily_basic():
    """Test basic Tavily search"""
    with respx.mock:
        respx.post("https://api.tavily.com/search").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "title": "Example Result",
                            "url": "https://example.com",
                            "content": "This is an example content",
                        }
                    ]
                },
            )
        )

        serp = Tavily(api_key="test_key")
        resp = serp.serp("test query")
        assert len(resp.items) == 1
        assert resp.items[0].title == "Example Result"
        assert resp.items[0].link == "https://example.com"


def test_tavily_time_range():
    """Test that time_range is properly passed to Tavily API"""
    serp = Tavily(api_key="test_key")

    # Test each time range value
    options = SerpRequestOptions(time_range=TimeRange.DAY)
    params = serp.get_serp_params("test query", options=options)
    assert params["time_range"] == "d"

    options = SerpRequestOptions(time_range=TimeRange.WEEK)
    params = serp.get_serp_params("test query", options=options)
    assert params["time_range"] == "w"

    options = SerpRequestOptions(time_range=TimeRange.MONTH)
    params = serp.get_serp_params("test query", options=options)
    assert params["time_range"] == "m"

    options = SerpRequestOptions(time_range=TimeRange.YEAR)
    params = serp.get_serp_params("test query", options=options)
    assert params["time_range"] == "y"


def test_tavily_custom_date_range():
    """Test that custom date range is properly passed to Tavily"""
    serp = Tavily(api_key="test_key")

    options = SerpRequestOptions(date_start="2024-01-01", date_end="2024-12-31")
    params = serp.get_serp_params("test query", options=options)

    assert params["start_date"] == "2024-01-01"
    assert params["end_date"] == "2024-12-31"


def test_tavily_only_date_start():
    """Test that only date_start is properly passed"""
    serp = Tavily(api_key="test_key")

    options = SerpRequestOptions(date_start="2024-06-01")
    params = serp.get_serp_params("test query", options=options)

    assert params["start_date"] == "2024-06-01"
    assert "end_date" not in params


def test_tavily_only_date_end():
    """Test that only date_end is properly passed"""
    serp = Tavily(api_key="test_key")

    options = SerpRequestOptions(date_end="2024-12-31")
    params = serp.get_serp_params("test query", options=options)

    assert params["end_date"] == "2024-12-31"
    assert "start_date" not in params


def test_tavily_date_range_priority():
    """Test that custom date range takes priority over time_range"""
    serp = Tavily(api_key="test_key")

    options = SerpRequestOptions(time_range=TimeRange.WEEK, date_start="2024-01-01", date_end="2024-12-31")
    params = serp.get_serp_params("test query", options=options)

    # Custom date range should take priority
    assert params["start_date"] == "2024-01-01"
    assert params["end_date"] == "2024-12-31"
    assert "time_range" not in params


def test_tavily_max_results():
    """Test that num parameter maps to max_results"""
    serp = Tavily(api_key="test_key")

    params = serp.get_serp_params("test query", num=20)
    assert params["max_results"] == 20


def test_tavily_all_options():
    """Test that all options work together"""
    serp = Tavily(api_key="test_key")

    options = SerpRequestOptions(time_range=TimeRange.DAY, extra_options={"include_domains": ["example.com"]})

    params = serp.get_serp_params("test query", num=15, options=options)

    assert params["query"] == "test query"
    assert params["max_results"] == 15
    assert params["time_range"] == "d"
    assert params["include_domains"] == ["example.com"]
