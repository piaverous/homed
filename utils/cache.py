from cachetools import TTLCache

color_cache = TTLCache(maxsize=2, ttl=40)
sensor_cache = TTLCache(maxsize=2, ttl=120)
