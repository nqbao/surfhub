import os
from .model import *
from .valueserp import *
from .google import *


def get_serp(provider=None):
    provider = provider or os.environ.get("SERP_PROVIDER")
    if not provider:
        raise ValueError("Please provide a SERP provider")
     
    if provider == "valueserp":
        return ValueSerp()
    
    if provider == "google":
        return GoogleSerp()
    
    raise ValueError(f"Unknown provider: {provider}")

