#!/usr/bin/python3
# -*- coding: utf-8 -*-
import asyncio,unittest
from redys import Client


def async_test(coro):
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper

class Test(unittest.TestCase):

    @async_test
    async def test_ping(self):
        assert await Client().ping() == "pong"

    @async_test
    async def test_0(self):
        with Client() as c:
            assert await c.set("jo",42) == True
            assert await c.get("jo")==42

            assert await c.set("jo",[1,2,3]) == True
            assert await c.get("jo")==[1,2,3]

            assert await c.set("jo",(1,2,3)) == True
            assert await c.get("jo")==(1,2,3)


    @async_test
    async def test_1(self):
        c = Client()
        assert await c.get("xxx") == None

    @async_test
    async def test_2(self):
        r = Client()
        assert await r.set("kkk","v") == True

        assert await r.get("kkk") == "v"

        assert "kkk" in await r.keys()

        assert await r.delete("kkk") == True

        assert "kkk" not in await r.keys()

    @async_test
    async def test_3(self):
        r = Client()

        assert await r.subscribe("toto") ==True
        assert await r.publish("toto",42) == True
        assert await r.publish("toto","hello") == True

        assert await r.get_event("toto") ==42
        assert await r.get_event("toto") =="hello"
        assert await r.get_event("toto") ==None
        assert await r.publish("toto",99) == True
        assert await r.unsubscribe("toto")

    @async_test
    async def test_4(self):
        r1 = Client()
        r2 = Client()

        assert await r1.subscribe("toto") ==True
        assert await r2.publish("toto",42) == True
        assert await r2.publish("toto","hello") == True

        assert await r1.get_event("toto") ==42
        assert await r1.get_event("toto") =="hello"
        assert await r1.get_event("toto") ==None
        assert await r2.publish("toto",99) == True
        assert await r1.get_event("toto") ==99
        assert await r1.get_event("toto") ==None
        assert await r1.unsubscribe("toto")

    @async_test
    async def test_5(self):
        r1 = Client()
        assert await r1.publish("newtoto","hello") == False # nobody is subscribing that
        r2=Client()
        assert await r2.subscribe("newtoto") ==True
        assert await r1.publish("newtoto","hello") == True
        assert await r2.unsubscribe("newtoto") ==True

        assert await r2.get_event("newtoto") == None
        assert await r1.publish("newtoto","hello") == False # nobody is subscribing that

    @async_test
    async def test_6(self):
        r1 = Client()
        assert await r1.get_event("xxxxx") == None    # get without subscribe before ....

    @async_test
    async def test_7(self):
        r1 = Client()
        assert await r1.unsubscribe("xxxxx") == False  # unsubscribe without subscribe it before ....


    @async_test
    async def test_x(self):
        r1 = Client()
        r2 = Client()
        r3 = Client()
        assert await r1.set("yo",666) == True
        assert await r2.get("yo") == 666
        assert "yo" in await r3.keys()

    @async_test
    async def test_events_multi_clients(self):
        r1 = Client()
        r2 = Client()
        rp = Client()
        assert await r1.subscribe("mychannel")
        assert await r2.subscribe("mychannel")
        assert await rp.publish("mychannel","hello")
        assert await r1.get_event("mychannel")=="hello"
        assert await r1.unsubscribe("mychannel")
        assert await r1.get_event("mychannel")==None
        assert await r2.get_event("mychannel")=="hello"

    @async_test
    async def test_incdec(self):
        r = Client()
        await r.delete("val")
        assert await r.get("val")==None

        assert await r.incr("val")==1
        assert await r.get("val")==1

        assert await r.incr("val")==2
        assert await r.get("val")==2

        assert await r.decr("val")==1
        assert await r.get("val")==1

        await r.delete("val")
        assert await r.get("val")==None

        await r.decr("val")
        assert await r.get("val")==-1

    @async_test
    async def test_queue_delete(self):
        r = Client()
        await r.delete("ll")
        await r.rpush("ll",42)==1
        assert await r.get("ll")==[42]
        assert await r.delete("ll")
        assert await r.get("ll")==None

    @async_test
    async def test_set_delete(self):
        r = Client()
        await r.delete("ll")
        await r.sadd("ll",42)==1
        assert await r.get("ll")=={42}
        assert await r.delete("ll")
        assert await r.get("ll")==None

    @async_test
    async def test_queues(self):
        r = Client()
        await r.delete("ll")
        assert await r.rpush("ll",42)==1
        assert await r.rpush("ll",43)==2
        assert await r.lpush("ll",41)==3
        assert await r.get("ll")==[41,42,43]
        assert await r.rpop("ll")==43
        assert await r.lpop("ll")==41
        assert await r.get("ll")==[42]
        assert await r.lpop("ll")==42
        assert await r.get("ll")==None
        assert await r.lpop("ll")==None
        assert await r.rpop("ll")==None

    @async_test
    async def test_try_queue_method_with_bad_type(self):
        r = Client()
        await r.set("kiki","hello")

        with self.assertRaises(Exception) as context:
            await r.rpop("kiki")

        with self.assertRaises(Exception) as context:
            await r.rpush("kiki",42)

        assert await r.get("kiki")=="hello"



    @async_test
    async def test_cache(self):
        r = Client()
        await r.setex("kiki",0.05,"hello")
        assert await r.get("kiki")=="hello"
        await asyncio.sleep(0.05)
        assert await r.get("kiki")==None

    @async_test
    async def test_cache2(self):
        r = Client()
        await r.setex("kiki",0.05,42)
        assert await r.incr("kiki",6)==48
        assert await r.get("kiki")==48
        await asyncio.sleep(0.05)
        assert await r.get("kiki")==None


    @async_test
    async def test_cache3(self):
        r = Client()
        await r.setex("kiki",0.05,42)
        assert await r.incr("kiki",6)==48
        assert "kiki" in await r.keys()
        await asyncio.sleep(0.05)
        assert "kiki" not in await r.keys()



    @async_test
    async def test_try_incdec_method_with_bad_type(self):
        r = Client()
        await r.set("kiki","hello")

        with self.assertRaises(Exception) as context:
            await r.incr("kiki")
        with self.assertRaises(Exception) as context:
            await r.decr("kiki")

    @async_test
    async def test_multi(self):
        r = Client()
        await r.set("v1",11)
        await r.set("v2",22)
        assert await r.get("v1","v3","v2")==[11,None,22]
        assert await r.delete("v1","v3","v2")==True
        assert await r.get("v1","v3","v2")==[None,None,None]

    @async_test
    async def test_try_set_method_with_bad_type(self):
        r = Client()
        await r.delete("a_int","unknown")

        assert await r.set("a_int",42)
        with self.assertRaises(Exception) as context:
            await r.sadd("a_int",42)
        with self.assertRaises(Exception) as context:
            await r.srem("a_int",42)

        with self.assertRaises(Exception) as context:
            await r.srem("unknown",42)


    @async_test
    async def test_set_method(self):
        r = Client()
        await r.delete("a_set")

        assert await r.sadd("a_set",42)==1
        assert await r.sadd("a_set",43)==2
        assert await r.sadd("a_set",42)==2

        assert await r.get("a_set")==set( (43,42) )

        assert await r.srem("a_set",666)==2 # 666 not in set, len is the same

        assert await r.srem("a_set",42)==1
        assert await r.srem("a_set",42)==1
        assert await r.srem("a_set",43)==0


        with self.assertRaises(Exception) as context:
            await r.srem("a_set",43)       # the set is dead

        assert await r.get("a_set")==None


    @async_test
    async def test_cant_mutate_set(self):
        r = Client()
        await r.set("jo",{42,43})
        assert await r.get("jo")=={42,43}
        with self.assertRaises(Exception) as context:
            await r.srem("jo",42)   # jo is a real set, not a redys set

        with self.assertRaises(Exception) as context:
            await r.sadd("jo",44)   # jo is a real set, not a redys set


    @async_test
    async def test_cant_mutate_queue(self):
        r = Client()
        await r.set("jo",[42,43])
        assert await r.get("jo")==[42,43]
        with self.assertRaises(Exception) as context:
            await r.rpush("jo",44)

        with self.assertRaises(Exception) as context:
            await r.lpush("jo",44)

        with self.assertRaises(Exception) as context:
            await r.rpop("jo")

        with self.assertRaises(Exception) as context:
            await l.rpop("jo")
import time
if __name__=="__main__":
    unittest.main()
    #~ async def kif():
        #~ r=Client()
        #~ print("!!!",r.set("ko",23))
        #~ print("!!!",r.get("ko"))

    #~ loop=asyncio.get_event_loop()
    #~ loop.run_until_complete( kif() )

    #~ r=Client()
    #~ for i in range(10):
        #~ r.delete("ll")
        #~ assert r.rpush("ll",42)==1
        #~ assert r.rpush("ll",43)==2
        #~ assert r.lpush("ll",41)==3
        #~ assert r.get("ll")==[41,42,43]
        #~ assert r.rpop("ll")==43
        #~ assert r.lpop("ll")==41
        #~ assert r.get("ll")==[42]
        #~ assert r.lpop("ll")==42
        #~ assert r.get("ll")==None
        #~ assert r.lpop("ll")==None
        #~ assert r.rpop("ll")==None

    #~ r1=Client()
    #~ r2=Client()
    #~ r1.rpush("x",1)
    #~ r1.rpush("x",2)
    #~ r1.rpush("x",3)
    #~ r1.rpush("x",4)
    #~ print( r2.lpop("x") )
    #~ print( r2.lpop("x") )
    #~ r1.rpush("x",5)
    #~ print( r2.lpop("x") )

