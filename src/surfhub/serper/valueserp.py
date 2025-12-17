from typing import List
from datetime import datetime
from .model import SerpResult, BaseSerper

class ValueSerp(BaseSerper):
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
            
            # Handle time filtering - custom date range takes priority
            if options.date_start or options.date_end:
                params["time_period"] = "custom"
                if options.date_start:
                    # Convert YYYY-MM-DD to MM/DD/YYYY
                    date_obj = datetime.strptime(options.date_start, "%Y-%m-%d")
                    params["time_period_min"] = date_obj.strftime("%m/%d/%Y")
                if options.date_end:
                    # Convert YYYY-MM-DD to MM/DD/YYYY
                    date_obj = datetime.strptime(options.date_end, "%Y-%m-%d")
                    params["time_period_max"] = date_obj.strftime("%m/%d/%Y")
            elif options.time_range:
                # Map TimeRange enum to ValueSerp time_period values
                time_range_map = {
                    "d": "last_day",
                    "w": "last_week",
                    "m": "last_month",
                    "y": "last_year"
                }
                params["time_period"] = time_range_map.get(options.time_range.value, options.time_range.value)
                
            # anything to pass to the API
            if options.extra_options:
                params.update(options.extra_options)
            # params['include_answer_box'] = 'true'
            # params['include_ai_overview'] = 'true'

        # include some reasonable defaults
        if "hl" not in params:
            params["hl"] = "en"

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
