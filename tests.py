from redys import Client

import unittest,asyncio

class ContextTestCase(unittest.TestCase):

    def test_0(self):
        with Client() as r:
            r.get("xxx") == None

    def test_1(self):
        r = Client()
        assert r.get("xxx") == None

    def test_2(self):
        r = Client()
        assert r.set("kkk","v") == True

        assert r.get("kkk") == "v"
        assert r.get("kkk","jjjj") == ["v",None]

        assert "kkk" in r.keys()

        assert r.delete("kkk","jjjj") == True

        assert "kkk" not in r.keys()


    def test_3(self):
        r = Client()

        assert r.register("toto") ==True
        assert r.publish("toto",42) == True
        assert r.publish("toto","hello") == True

        assert r.subscribe("toto") ==42
        assert r.subscribe("toto") =="hello"
        assert r.subscribe("toto") ==None
        assert r.publish("toto",99) == True
        #~ assert r.unregister("toto")


    def test_3(self):
        r1 = Client()
        r2 = Client()

        assert r1.register("toto") ==True
        assert r2.publish("toto",42) == True
        assert r2.publish("toto","hello") == True

        assert r1.subscribe("toto") ==42
        assert r1.subscribe("toto") =="hello"
        assert r1.subscribe("toto") ==None
        assert r2.publish("toto",99) == True
        assert r1.subscribe("toto") ==99
        assert r1.subscribe("toto") ==None
        #~ assert r1.unregister("toto")

    def test_4(self):
        r1 = Client()
        assert r1.publish("toto","hello") == False # nobody is subscribing that
        r2=Client()
        assert r2.register("toto") ==True
        assert r1.publish("toto","hello") == True
        assert r2.unregister("toto") ==True

        assert r2.subscribe("toto") == None
        assert r1.publish("toto","hello") == False # nobody is subscribing that

    def test_5(self):
        r1 = Client()
        assert r1.subscribe("xxxxx") == None    # subscribe without register ....

    def test_6(self):
        r1 = Client()
        assert r1.unregister("xxxxx") == False  # unregister without register it before ....

    def test_x(self):
        r1 = Client()
        r2 = Client()
        r3 = Client()
        assert r1.set("yo",666) == True
        assert r2.get("yo") == 666
        assert "yo" in r3.keys()

if __name__=="__main__":
    unittest.main()
