import respx
import httpx
from surfhub.serper.serpapi import SerpApi
from surfhub.serper.model import SerpRequestOptions, TimeRange


def test_serpapi_basic():
    """Test basic SerpApi search"""
    with respx.mock:
        respx.get("https://serpapi.com/search").mock(
            return_value=httpx.Response(
                200, 
                json={
                    "search_metadata": {
                        "status": "Success"
                    },
                    "organic_results": [
                        {
                            "title": "Example Result",
                            "link": "https://example.com",
                            "snippet": "This is an example snippet",
                            "displayed_link": "example.com › page"
                        }
                    ]
                }
            )
        )
        
        serp = SerpApi(api_key="test_key")
        resp = serp.serp("test query")
        assert len(resp.items) == 1
        assert resp.items[0].title == "Example Result"
        assert resp.items[0].link == "https://example.com"


def test_serpapi_time_range():
    """Test that time_range is properly mapped to SerpApi's tbs parameter"""
    serp = SerpApi(api_key="test_key")
    
    # Test each time range mapping
    options = SerpRequestOptions(time_range=TimeRange.DAY)
    params = serp.get_serp_params("test query", options=options)
    assert params["tbs"] == "qdr:d"
    
    options = SerpRequestOptions(time_range=TimeRange.WEEK)
    params = serp.get_serp_params("test query", options=options)
    assert params["tbs"] == "qdr:w"
    
    options = SerpRequestOptions(time_range=TimeRange.MONTH)
    params = serp.get_serp_params("test query", options=options)
    assert params["tbs"] == "qdr:m"
    
    options = SerpRequestOptions(time_range=TimeRange.YEAR)
    params = serp.get_serp_params("test query", options=options)
    assert params["tbs"] == "qdr:y"


def test_serpapi_custom_date_range():
    """Test that custom date range is properly formatted for SerpApi"""
    serp = SerpApi(api_key="test_key")
    
    options = SerpRequestOptions(
        date_start="2024-01-01",
        date_end="2024-12-31"
    )
    params = serp.get_serp_params("test query", options=options)
    
    assert "tbs" in params
    assert "cdr:1" in params["tbs"]
    assert "cd_min:01/01/2024" in params["tbs"]
    assert "cd_max:12/31/2024" in params["tbs"]


def test_serpapi_only_date_start():
    """Test that only date_start creates proper tbs parameter"""
    serp = SerpApi(api_key="test_key")
    
    options = SerpRequestOptions(date_start="2024-06-01")
    params = serp.get_serp_params("test query", options=options)
    
    assert "tbs" in params
    assert "cdr:1" in params["tbs"]
    assert "cd_min:06/01/2024" in params["tbs"]
    assert "cd_max:" in params["tbs"]  # Should have today's date


def test_serpapi_only_date_end():
    """Test that only date_end creates proper tbs parameter"""
    serp = SerpApi(api_key="test_key")
    
    options = SerpRequestOptions(date_end="2024-12-31")
    params = serp.get_serp_params("test query", options=options)
    
    assert "tbs" in params
    assert "cdr:1" in params["tbs"]
    assert "cd_min:01/01/2000" in params["tbs"]
    assert "cd_max:12/31/2024" in params["tbs"]


def test_serpapi_date_range_priority():
    """Test that custom date range takes priority over time_range"""
    serp = SerpApi(api_key="test_key")
    
    options = SerpRequestOptions(
        time_range=TimeRange.WEEK,
        date_start="2024-01-01",
        date_end="2024-12-31"
    )
    params = serp.get_serp_params("test query", options=options)
    
    # Custom date range should take priority
    assert "tbs" in params
    assert "cdr:1" in params["tbs"]
    assert "cd_min:01/01/2024" in params["tbs"]
    assert "cd_max:12/31/2024" in params["tbs"]


def test_serpapi_pagination():
    """Test that pagination uses start parameter"""
    serp = SerpApi(api_key="test_key")
    
    # Page 1 should have start=0
    params = serp.get_serp_params("test query", page=1, num=10)
    assert params["start"] == 0
    
    # Page 2 should have start=10
    params = serp.get_serp_params("test query", page=2, num=10)
    assert params["start"] == 10
    
    # Page 3 should have start=20
    params = serp.get_serp_params("test query", page=3, num=10)
    assert params["start"] == 20


def test_serpapi_all_options():
    """Test that all options are properly set"""
    serp = SerpApi(api_key="test_key")
    
    options = SerpRequestOptions(
        lang="en",
        country="us",
        location="New York,United States",
        google_domain="google.com",
        time_range=TimeRange.DAY,
        extra_options={"safe": "active"}
    )
    
    params = serp.get_serp_params("test query", page=1, num=20, options=options)
    
    assert params["q"] == "test query"
    assert params["api_key"] == "test_key"
    assert params["engine"] == "google"
    assert params["hl"] == "en"
    assert params["gl"] == "us"
    assert params["location"] == "New York,United States"
    assert params["google_domain"] == "google.com"
    assert params["tbs"] == "qdr:d"
    assert params["num"] == 20
    assert params["start"] == 0
    assert params["safe"] == "active"


def test_serpapi_error_handling():
    """Test error handling for SerpApi errors"""
    with respx.mock:
        respx.get("https://serpapi.com/search").mock(
            return_value=httpx.Response(
                200, 
                json={
                    "error": "Invalid API key"
                }
            )
        )
        
        serp = SerpApi(api_key="invalid_key")
        try:
            resp = serp.serp("test query")
            assert False, "Should have raised an exception"
        except Exception as e:
            assert "SerpApi error" in str(e)
            assert "Invalid API key" in str(e)
