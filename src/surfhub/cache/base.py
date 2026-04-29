import diskcache

__all__ = ["Cache", "DummyCache", "FileCache"]

class Cache:
    def get(self, key: str):
        raise NotImplementedError()
    
    def set(self, key: str, value, ttl: int = None):
        raise NotImplementedError()
    
    def has(self, key: str) -> bool:
        return self.get(key) is not None
    
    def delete(self, key: str):
        raise NotImplementedError()
    
    def clear(self):
        raise NotImplementedError()


class DummyCache(Cache):
    def get(self, key: str):
        return None
    
    def set(self, key: str, value, ttl: int = None):
        return None
    
    def delete(self, key: str):
        return None
    
    def clear(self):
        return None


class FileCache(Cache):
    def __init__(self, cache_dir: str, default_ttl: int = 3600):
        self.cache = diskcache.Cache(cache_dir)
        self.ttl = default_ttl
    
    def get(self, key: str):
        return self.cache.get(key)
    
    def set(self, key: str, value, ttl: int = None):
        self.cache.set(key, value, expire=ttl or self.ttl)
    
    def delete(self, key: str):
        self.cache.pop(key, None)

    def clear(self):
        self.cache.clear()
