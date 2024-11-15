from typing import List, Optional
from .model import *
import httpx
from surfhub.utils import hash_dict

class GoogleSerp(BaseSerp):
    """
    Search Google via Google Custom Search API
    """
    
    default_api_url = "https://www.googleapis.com/customsearch/v1"
    
    def serp(self, query : str, page = None, num = None, options : Optional[SerpRequestOptions] = None) -> List[SerpResult]:
        params = {
            "q": query,
        }
        
        if not self.api_key:
            raise ValueError("Please provide a Google API key")
        if ":" not in self.api_key:
            raise ValueError("Please provider api key in the format cx:key")

        cx, key = self.api_key.split(":", 2)
        params["key"] = key
        params["cx"] = cx
        
        if options:
            if options.lang:
                params["hl"] = options.lang
                
            if options.country:
                params["gl"] = options.country
                
            if options.extra_options:
                params.update(options.extra_options)
                
        if page is not None:
            params["page"] = page
            
        if num is not None:
            params["num"] = num
        
        cache_key = None
        resp = None
        if self.cache:
            cache_key = hash_dict({**params, "endpoint": self.endpoint})
            resp = self.cache.get(cache_key)
        
        if resp is None:
            resp = httpx.get(self.endpoint, params=params, timeout=self.timeout).json()
        
        if not resp['request_info']['success']:
            raise Exception(resp['request_info']['message'])
        
        if self.cache and cache_key:
            self.cache.set(cache_key, resp)
        
        return [
            SerpResult(
                title=i.get("title"),
                link=i.get("link"),
                snippet=i.get("snippet", ""),
                prefix=i.get("prefix", "")
            )
            for i in resp['items']
        ]
