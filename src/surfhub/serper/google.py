from .model import BaseSerp, SerpResult

class GoogleCustomSearch(BaseSerp):
    """
    Search Google via Google Custom Search API
    """
    
    default_api_url = "https://www.googleapis.com/customsearch/v1"
    
    def get_serp_params(self, query, page=None, num=None, options = None):
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

        return params
    
    def parse_result(self, resp):
        if 'error' in resp:
            raise RuntimeError(resp['error']['message'])

        return [
            SerpResult(
                title=i.get("title"),
                link=i.get("link"),
                snippet=i.get("snippet", ""),
                prefix=i.get("prefix", "")
            )
            for i in resp['items']
        ]
