from cachetools import TTLCache

# Create a TTL cache for ip geo results
# maxsize = 2000, ttl = 5 days
ipResultCache = TTLCache(maxsize=2000, ttl=5 * 24 * 60 * 60)
