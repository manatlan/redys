# redys

A simple redis-like in pure python3, fully asyncio/thread/process compliant !

[on pypi/redys](https://pypi.org/project/redys/)

### features

- asyncio compliant
- client Sync (Client) & Async (AClient)
- 100% tested on all platforms ("3.7", "3.8", "3.9", "3.10", "3.11" on  ubuntu-latest, macos-latest, windows-latest) **NEW**
- very quick
- `classics` commands : get/set/delete/keys & incr/decr
- `sets` commands : sadd/srem
- `queue` commands : rpush/lpush/rpop/lpop
- `pubsub` commands : subscribe/unsubscribe/get_event & publish
- `cache` commands : setex
- `ping()` command ;-)
- `KILL()` command (so a client can kill the server) **NEW**
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

- The sync client (`Client`) use threads, so it can't live in the same loop as the server (`Server`). It's better to use it in another thread or process.
- The async client (`AClient`) can live in the same loop as the server (`Server`), but don't forget to await each methods (which are coroutines in async version)
- Not fully/concurrency tested. Use at own risk ;-)
- See [tests](https://github.com/manatlan/redys/blob/master/tests.py) for examples

BTW, I use it in production since 2018: and no problems at all !!!! (it works as excepted)
