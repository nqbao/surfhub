import respx
import httpx
from surfhub.serper.valueserp import ValueSerp


def test_valueserp():
    with respx.mock:
        respx.get("https://api.valueserp.com/search?q=how%20to%20make%20cookie&api_key=123456").mock(
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
