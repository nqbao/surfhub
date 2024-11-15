import diskcache

class Cache:
    def get(self, key):
        raise NotImplementedError()
    
    def set(self, key, value, ttl=None):
        raise NotImplementedError()
    
    def has(self, key):
        return self.get(key) is not None
    
    def delete(self, key):
        raise NotImplementedError()
    
    def clear(self):
        raise NotImplementedError()


class DummyCache(Cache):
    def get(self, key):
        return None
    
    def set(self, key, value, ttl=None):
        return None
    
    def delete(self, key):
        return None
    
    def clear(self):
        return None


class FileCache(Cache):
    def __init__(self, cache_dir, default_ttl=3600):
        self.cache = diskcache.Cache(cache_dir)
        self.ttl = default_ttl
    
    def get(self, key):
        return self.cache.get(key)
    
    def set(self, key, value, ttl=None):
        self.cache.set(key, value, expire=ttl or self.ttl)
    
    def delete(self, key):
        self.cache.pop(key, None)

    def clear(self):
        self.cache.clear()
