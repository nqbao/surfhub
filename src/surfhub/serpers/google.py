import os
from typing import List, Optional
from .model import *
import httpx

class GoogleSerp(BaseSerp):
    default_api_url = "https://www.googleapis.com/customsearch/v1"
    
    def serp(self, query : str, page = None, num = None, options : Optional[SerpRequestOptions] = None) -> List[SerpResult]:
        params = {
            "q": query,
        }
        
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
        
        resp = httpx.get(self.endpoint, params=params, timeout=self.timeout).json()
        
        return [
            SerpResult(
                title=i.get("title"),
                link=i.get("link"),
                snippet=i.get("snippet", ""),
                prefix=i.get("prefix", "")
            )
            for i in resp['items']
        ]
