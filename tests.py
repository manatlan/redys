import asyncio,unittest
from redys import Client


def async_test(coro):
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper

class Test(unittest.TestCase):

    @async_test
    async def test_0(self):
        with Client() as c:
            assert await c.set("jo",42) == True
            print( await c.get("jo") )
            assert await c.get("jo")==42

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
    async def test_multi(self):
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

        await r.incr("val")
        assert await r.get("val")==1

        await r.incr("val")
        assert await r.get("val")==2

        await r.decr("val")
        assert await r.get("val")==1

        await r.delete("val")
        assert await r.get("val")==None

        await r.decr("val")
        assert await r.get("val")==-1

    @async_test
    async def test_pushpop(self):
        r = Client()
        assert await r.delete("ll")
        assert await r.rpush("ll",42)==1
        assert await r.rpush("ll",43)==2
        assert await r.lpush("ll",41)==3
        assert await r.get("ll")==[41,42,43]
        assert await r.rpop("ll")==43
        assert await r.get("ll")==[41,42]
        assert await r.lpop("ll")==41
        assert await r.get("ll")==[42]
        assert await r.lpop("ll")==42
        assert await r.get("ll")==[]
        assert await r.lpop("ll")==None
        assert await r.get("ll")==[]

    @async_test
    async def test_pushpop(self):
        r = Client()
        await r.set("kiki","hello")
        assert await r.rpush("kiki",42)==2 # kiki becomes a list
        assert await r.get("kiki")==["hello",42]


if __name__=="__main__":
    unittest.main()

