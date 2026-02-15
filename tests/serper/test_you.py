import respx
import httpx
from surfhub.serper.you import YouSearch
from surfhub.serper.model import SerpRequestOptions, TimeRange


def test_you_basic():
    """Test basic You.com search"""
    with respx.mock:
        respx.get("https://ydc-index.io/v1/search").mock(
            return_value=httpx.Response(
                200, 
                json={
                    "results": {
                        "web": [
                            {
                                "url": "https://example.com/article",
                                "title": "Article Title",
                                "description": "Brief description of the content",
                                "snippets": [
                                    "Relevant excerpt from the page",
                                    "Another relevant passage"
                                ]
                            }
                        ]
                    },
                    "metadata": {
                        "search_uuid": "test-uuid",
                        "query": "test query",
                        "latency": 0.342
                    }
                }
            )
        )
        
        serp = YouSearch(api_key="test_key")
        resp = serp.serp("test query")
        assert len(resp.items) == 1
        assert resp.items[0].title == "Article Title"
        assert resp.items[0].link == "https://example.com/article"
        assert "Relevant excerpt" in resp.items[0].snippet


def test_you_web_and_news():
    """Test You.com search with both web and news results"""
    with respx.mock:
        respx.get("https://ydc-index.io/v1/search").mock(
            return_value=httpx.Response(
                200, 
                json={
                    "results": {
                        "web": [
                            {
                                "url": "https://example.com/article",
                                "title": "Web Article",
                                "description": "Web content",
                                "snippets": ["Web snippet"]
                            }
                        ],
                        "news": [
                            {
                                "title": "Breaking News",
                                "description": "News summary",
                                "url": "https://news.com/article"
                            }
                        ]
                    }
                }
            )
        )
        
        serp = YouSearch(api_key="test_key")
        resp = serp.serp("test query")
        assert len(resp.items) == 2
        assert resp.items[0].title == "Web Article"
        assert resp.items[0].prefix == ""
        assert resp.items[1].title == "Breaking News"
        assert resp.items[1].prefix == "[News]"


def test_you_params():
    """Test parameter mapping"""
    serp = YouSearch(api_key="test_key")
    
    # Test num parameter
    params = serp.get_serp_params("test query", num=20)
    assert params["count"] == 20
    
    # Test country parameter (should be uppercase)
    options = SerpRequestOptions(country="us")
    params = serp.get_serp_params("test query", options=options)
    assert params["country"] == "US"
    
    # Test language parameter (should be uppercase)
    options = SerpRequestOptions(lang="en")
    params = serp.get_serp_params("test query", options=options)
    assert params["language"] == "EN"
    
    # Test extra options
    options = SerpRequestOptions(extra_options={"safesearch": "strict"})
    params = serp.get_serp_params("test query", options=options)
    assert params["safesearch"] == "strict"


def test_you_empty_results():
    """Test handling of empty results"""
    with respx.mock:
        respx.get("https://ydc-index.io/v1/search").mock(
            return_value=httpx.Response(
                200, 
                json={
                    "results": {},
                    "metadata": {
                        "search_uuid": "test-uuid",
                        "query": "test query"
                    }
                }
            )
        )
        
        serp = YouSearch(api_key="test_key")
        resp = serp.serp("test query")
        assert len(resp.items) == 0


def test_you_snippets_fallback():
    """Test that description is used when snippets are not available"""
    with respx.mock:
        respx.get("https://ydc-index.io/v1/search").mock(
            return_value=httpx.Response(
                200, 
                json={
                    "results": {
                        "web": [
                            {
                                "url": "https://example.com",
                                "title": "Example",
                                "description": "Description text"
                            }
                        ]
                    }
                }
            )
        )
        
        serp = YouSearch(api_key="test_key")
        resp = serp.serp("test query")
        assert resp.items[0].snippet == "Description text"


def test_you_time_filtering():
    """Test time filtering with freshness parameter"""
    serp = YouSearch(api_key="test_key")
    
    # Test TimeRange mapping
    options = SerpRequestOptions(time_range=TimeRange.DAY)
    params = serp.get_serp_params("test query", options=options)
    assert params["freshness"] == "day"
    
    options = SerpRequestOptions(time_range=TimeRange.WEEK)
    params = serp.get_serp_params("test query", options=options)
    assert params["freshness"] == "week"
    
    options = SerpRequestOptions(time_range=TimeRange.MONTH)
    params = serp.get_serp_params("test query", options=options)
    assert params["freshness"] == "month"
    
    options = SerpRequestOptions(time_range=TimeRange.YEAR)
    params = serp.get_serp_params("test query", options=options)
    assert params["freshness"] == "year"
    
    # Test custom date range
    options = SerpRequestOptions(date_start="2025-01-01", date_end="2025-12-31")
    params = serp.get_serp_params("test query", options=options)
    assert params["freshness"] == "2025-01-01to2025-12-31"


def test_you_pagination():
    """Test pagination with offset parameter"""
    serp = YouSearch(api_key="test_key")
    
    params = serp.get_serp_params("test query", page=2)
    assert params["offset"] == 2
