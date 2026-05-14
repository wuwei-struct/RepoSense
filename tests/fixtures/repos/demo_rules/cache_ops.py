from django.core.cache import cache
def f():
    cache.set("k", "v")
    cache.get("k")

def g(redis_client):
    redis_client.set("k", "v")
    redis_client.get("k")
