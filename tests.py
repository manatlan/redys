import asyncio,unittest
from redys import Client


def async_test(coro):
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper

class Test(unittest.TestCase):

    @async_test
    async def test_xxx(self):
        c=Client()
        r=await c.set("jo",42)
        c2=Client()
        r=await c2.get("jo")


    @async_test
    async def test_1(self):
        c = Client()
        assert await c.get("xxx") == None

    @async_test
    async def test_2(self):
        r = Client()
        assert await r.set("kkk","v") == True

        assert await r.get("kkk") == "v"
        assert await r.get("kkk","jjjj") == ["v",None]

        assert "kkk" in await r.keys()

        assert await r.delete("kkk","jjjj") == True

        assert "kkk" not in await r.keys()

    @async_test
    async def test_3(self):
        r = Client()

        assert await r.register("toto") ==True
        assert await r.publish("toto",42) == True
        assert await r.publish("toto","hello") == True

        assert await r.subscribe("toto") ==42
        assert await r.subscribe("toto") =="hello"
        assert await r.subscribe("toto") ==None
        assert await r.publish("toto",99) == True
        assert await r.unregister("toto")

    @async_test
    async def test_4(self):
        r1 = Client()
        r2 = Client()

        assert await r1.register("toto") ==True
        assert await r2.publish("toto",42) == True
        assert await r2.publish("toto","hello") == True

        assert await r1.subscribe("toto") ==42
        assert await r1.subscribe("toto") =="hello"
        assert await r1.subscribe("toto") ==None
        assert await r2.publish("toto",99) == True
        assert await r1.subscribe("toto") ==99
        assert await r1.subscribe("toto") ==None
        assert await r1.unregister("toto")

    @async_test
    async def test_5(self):
        r1 = Client()
        assert await r1.publish("newtoto","hello") == False # nobody is subscribing that
        r2=Client()
        assert await r2.register("newtoto") ==True
        assert await r1.publish("newtoto","hello") == True
        assert await r2.unregister("newtoto") ==True

        assert await r2.subscribe("newtoto") == None
        assert await r1.publish("newtoto","hello") == False # nobody is subscribing that

    @async_test
    async def test_6(self):
        r1 = Client()
        assert await r1.subscribe("xxxxx") == None    # subscribe without register ....

    @async_test
    async def test_7(self):
        r1 = Client()
        assert await r1.unregister("xxxxx") == False  # unregister without register it before ....


    @async_test
    async def test_x(self):
        r1 = Client()
        r2 = Client()
        r3 = Client()
        assert await r1.set("yo",666) == True
        assert await r2.get("yo") == 666
        assert "yo" in await r3.keys()


if __name__=="__main__":
    unittest.main()


