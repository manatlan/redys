# redys
A simple redis-like in pure python3, fully asyncio compliant !

### features

- asyncio compliant
- client sync methods
- very quick
- classic commands : get/set/delete/keys & incr/decr
- sets commands : sadd/srem
- queue commands : rpush/lpush/rpop/lpop
- pubsub commands : subscribe/unsubscribe/get_event & publish
- cache commands : setex
- ping command ;-)
- exchange everything that is pickable (except None)
- raise real python exception in client side
- minimal code size
- works well on GAE Standard (2nd generation/py37)
- just in-memory !

### why ?

Redis is great, but overbloated for my needs. Redys is simple, you can start
the server side in an asyncio loop, and clients can interact with a simple
in-memory db. Really useful when clients are in
async/threads/process(workers)/multi-hosts world, to share a unique source of truth.

### nb

- Not fully/concurrency tested. Use at own risk ;-)

