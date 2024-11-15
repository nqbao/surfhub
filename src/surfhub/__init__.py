from typing import List, Optional
from surfhub.serpers import get_serp, SerpResult, SerpRequestOptions

def serp(query : str, page : int = None, num : int = None, options : Optional[SerpRequestOptions] = None) -> List[SerpResult]:
    return get_serp().serp(query, options=options, page=page, num=num)
