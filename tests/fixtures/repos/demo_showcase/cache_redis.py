import redis
def do_cache():
    r = redis.Redis()
    r.set('k','v')
    return r.get('k')
