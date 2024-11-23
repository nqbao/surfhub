from typing import List, Optional
import os
import httpx
from .model import SerpRequestOptions, SerpResult, BaseSerp

class ValueSerp(BaseSerp):
    default_api_url = "https://api.valueserp.com/search"
    
    def serp(self, query : str, page = None, num = None, options : Optional[SerpRequestOptions] = None) -> List[SerpResult]:
        params = {
            "q": query,
            "api_key": self.api_key
        }
        
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
        
        if not resp['request_info']['success']:
            raise Exception(resp['request_info']['message'])

        return [
            SerpResult(
                title=i.get("title"),
                link=i.get("link"),
                snippet=i.get("snippet", ""),
                prefix=i.get("prefix", "")
            )
            for i in resp['organic_results']
        ]
