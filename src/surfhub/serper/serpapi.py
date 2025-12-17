from typing import List
from datetime import datetime
from .model import SerpResult, BaseSerper


class SerpApi(BaseSerper):
    """
    Search Google via SerpApi (serpapi.com)
    """
    
    default_api_url = "https://serpapi.com/search"
    
    def get_serp_params(self, query, page=None, num=None, options=None):
        params = {
            "q": query,
            "api_key": self.api_key,
            "engine": "google"  # Default to Google search
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
                # SerpApi uses tbs parameter for custom date ranges
                if options.date_start and options.date_end:
                    # Convert YYYY-MM-DD to Google's custom date range format
                    start_obj = datetime.strptime(options.date_start, "%Y-%m-%d")
                    end_obj = datetime.strptime(options.date_end, "%Y-%m-%d")
                    start_formatted = start_obj.strftime("%m/%d/%Y")
                    end_formatted = end_obj.strftime("%m/%d/%Y")
                    params["tbs"] = f"cdr:1,cd_min:{start_formatted},cd_max:{end_formatted}"
                elif options.date_start:
                    # Only start date
                    start_obj = datetime.strptime(options.date_start, "%Y-%m-%d")
                    start_formatted = start_obj.strftime("%m/%d/%Y")
                    today = datetime.now().strftime("%m/%d/%Y")
                    params["tbs"] = f"cdr:1,cd_min:{start_formatted},cd_max:{today}"
                elif options.date_end:
                    # Only end date
                    end_obj = datetime.strptime(options.date_end, "%Y-%m-%d")
                    end_formatted = end_obj.strftime("%m/%d/%Y")
                    params["tbs"] = f"cdr:1,cd_min:01/01/2000,cd_max:{end_formatted}"
            elif options.time_range:
                # Map TimeRange enum to SerpApi tbs parameter
                time_range_map = {
                    "d": "qdr:d",  # Past day
                    "w": "qdr:w",  # Past week
                    "m": "qdr:m",  # Past month
                    "y": "qdr:y"   # Past year
                }
                params["tbs"] = time_range_map.get(options.time_range.value, options.time_range.value)
                
            # anything to pass to the API
            if options.extra_options:
                params.update(options.extra_options)

        # include some reasonable defaults
        if "hl" not in params:
            params["hl"] = "en"

        if page is not None:
            # SerpApi uses 'start' parameter for pagination
            # start = (page - 1) * num_results
            params["start"] = (page - 1) * (num or 10)
            
        if num is not None:
            params["num"] = num
            
        return params
    
    def parse_result(self, resp) -> List[SerpResult]:
        # Check for errors
        if "error" in resp:
            raise Exception(f"SerpApi error: {resp['error']}")
        
        # Parse organic results
        organic_results = resp.get("organic_results", [])
        
        return [
            SerpResult(
                title=i.get("title", ""),
                link=i.get("link", ""),
                snippet=i.get("snippet", ""),
                prefix=i.get("displayed_link", "").split("/")[0] if i.get("displayed_link") else ""
            )
            for i in organic_results
        ]
