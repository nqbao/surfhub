from typing import List, Optional
import httpx
from .model import SerpRequestOptions, SerpResult, BaseSerp
from surfhub.utils import hash_dict

class SerperDev(BaseSerp):
    """
    Search Google via serper.dev API
    """
    
    default_api_url = "https://google.serper.dev/search"
    
    def serp(self, query : str, page = None, num = None, options : Optional[SerpRequestOptions] = None) -> List[SerpResult]:
        params = {
            "q": query,
            "apiKey": self.api_key
        }
        
        if options:
            if options.lang:
                params["hl"] = options.lang
                
            if options.country:
                params["gl"] = options.country
                
            if options.location:
                params["location"] = options.location
                
            if options.google_domain:
                params["google_domain"] = options.google_domain
                
            # anything to pass to the API
            if options.extra_options:
                params.update(options.extra_options)
            # params['include_answer_box'] = 'true'

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

        if self.cache and cache_key:
            self.cache.set(cache_key, resp)

        return [
            SerpResult(
                title=i.get("title"),
                link=i.get("link"),
                snippet=i.get("snippet", ""),
                prefix=i.get("prefix", "")
            )
            for i in resp['organic']
        ]