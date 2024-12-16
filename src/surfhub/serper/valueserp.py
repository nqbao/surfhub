from typing import List
from .model import SerpResult, BaseSerp

class ValueSerp(BaseSerp):
    """
    Search Google via ValueSerp API
    """
    
    default_api_url = "https://api.valueserp.com/search"
    
    def get_serp_params(self, query, page=None, num=None, options = None):
        params = {
            "q": query,
            "api_key": self.api_key
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
            
        return params
    
    def parse_result(self, resp) -> List[SerpResult]:
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
