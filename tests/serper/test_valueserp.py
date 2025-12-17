import respx
import httpx
from surfhub.serper.valueserp import ValueSerp
from surfhub.serper.model import SerpRequestOptions, TimeRange


def test_valueserp():
    with respx.mock:
        respx.get("https://api.valueserp.com/search?q=how%20to%20make%20cookie&api_key=123456&hl=en").mock(
            return_value=httpx.Response(
                200, 
                json={
                    "request_info": {
                        "success": True,
                    },
                    "organic_results": [
                        {
                            "title": "How to make cookie",
                            "link": "https://example.com",
                            "snippet": "This is a cookie recipe",
                            "prefix": ""
                        }
                    ]
                }
            )
        )
        
        serp = ValueSerp(api_key="123456")
        resp = serp.serp("how to make cookie")
        assert len(resp.items) == 1


def test_valueserp_time_range():
    """Test that time_range is properly mapped to ValueSerp's time_period parameter"""
    serp = ValueSerp(api_key="123456")
    
    # Test each time range mapping
    options = SerpRequestOptions(time_range=TimeRange.DAY)
    params = serp.get_serp_params("test query", options=options)
    assert params["time_period"] == "last_day"
    
    options = SerpRequestOptions(time_range=TimeRange.WEEK)
    params = serp.get_serp_params("test query", options=options)
    assert params["time_period"] == "last_week"
    
    options = SerpRequestOptions(time_range=TimeRange.MONTH)
    params = serp.get_serp_params("test query", options=options)
    assert params["time_period"] == "last_month"
    
    options = SerpRequestOptions(time_range=TimeRange.YEAR)
    params = serp.get_serp_params("test query", options=options)
    assert params["time_period"] == "last_year"


def test_valueserp_custom_date_range():
    """Test that custom date range is properly formatted for ValueSerp"""
    serp = ValueSerp(api_key="123456")
    
    options = SerpRequestOptions(
        date_start="2024-01-01",
        date_end="2024-12-31"
    )
    params = serp.get_serp_params("test query", options=options)
    
    assert params["time_period"] == "custom"
    assert params["time_period_min"] == "01/01/2024"
    assert params["time_period_max"] == "12/31/2024"


def test_valueserp_only_date_start():
    """Test that only date_start sets time_period_min"""
    serp = ValueSerp(api_key="123456")
    
    options = SerpRequestOptions(date_start="2024-06-01")
    params = serp.get_serp_params("test query", options=options)
    
    assert params["time_period"] == "custom"
    assert params["time_period_min"] == "06/01/2024"
    assert "time_period_max" not in params


def test_valueserp_only_date_end():
    """Test that only date_end sets time_period_max"""
    serp = ValueSerp(api_key="123456")
    
    options = SerpRequestOptions(date_end="2024-12-31")
    params = serp.get_serp_params("test query", options=options)
    
    assert params["time_period"] == "custom"
    assert params["time_period_max"] == "12/31/2024"
    assert "time_period_min" not in params


def test_valueserp_date_range_priority():
    """Test that custom date range takes priority over time_range"""
    serp = ValueSerp(api_key="123456")
    
    options = SerpRequestOptions(
        time_range=TimeRange.WEEK,
        date_start="2024-01-01",
        date_end="2024-12-31"
    )
    params = serp.get_serp_params("test query", options=options)
    
    # Custom date range should take priority
    assert params["time_period"] == "custom"
    assert params["time_period_min"] == "01/01/2024"
    assert params["time_period_max"] == "12/31/2024"
