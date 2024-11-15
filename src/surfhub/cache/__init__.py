import os
from .base import DummyCache, Cache, FileCache

def get_cache(provider=None, default_ttl=3600) -> Cache:
    provider = provider or os.environ.get('SURFHUB_CACHE')
    
    if provider == 'file':
        if not os.environ.get('SURFHUB_CACHE_DIR'):
            raise ValueError('SURFHUB_CACHE_DIR is required when using file cache')

        return FileCache(os.environ.get('SURFHUB_CACHE_DIR'), default_ttl=default_ttl)
    elif provider == 'dummy':
        return DummyCache()
    
    raise ValueError(f'Unknown cache provider: {provider}')
