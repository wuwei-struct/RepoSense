import redis
def do_cache():
    r = redis.Redis()
    r.set('k','v')
    r.set('k2','v2')
    return r.get('k')
