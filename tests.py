#!/usr/bin/python3
# -*- coding: utf-8 -*-
import asyncio,unittest,time
from redys import Client


def async_test(coro):
  def wrapper(*args, **kwargs):
    loop = asyncio.new_event_loop()
    return loop.run_until_complete(coro(*args, **kwargs))
  return wrapper

class Test(unittest.TestCase):

  def test_ping(self):
    assert Client().ping() == "pong"


  def test_0(self):
    with Client() as c:
      assert c.set("jo",42) == True
      assert c.get("jo")==42

      assert c.set("jo",[1,2,3]) == True
      assert c.get("jo")==[1,2,3]

      assert c.set("jo",(1,2,3)) == True
      assert c.get("jo")==(1,2,3)



  def test_1(self):
    c = Client()
    assert c.get("xxx") == None


  def test_2(self):
    r = Client()
    assert r.set("kkk","v") == True

    assert r.get("kkk") == "v"

    assert "kkk" in r.keys()

    assert r.delete("kkk") == True

    assert "kkk" not in r.keys()


  def test_3(self):
    r = Client()

    assert r.subscribe("toto") ==True
    assert r.publish("toto",42) == True
    assert r.publish("toto","hello") == True

    assert r.get_event("toto") ==42
    assert r.get_event("toto") =="hello"
    assert r.get_event("toto") ==None
    assert r.publish("toto",99) == True
    assert r.unsubscribe("toto")


  def test_4(self):
    r1 = Client()
    r2 = Client()

    assert r1.subscribe("toto") ==True
    assert r2.publish("toto",42) == True
    assert r2.publish("toto","hello") == True

    assert r1.get_event("toto") ==42
    assert r1.get_event("toto") =="hello"
    assert r1.get_event("toto") ==None
    assert r2.publish("toto",99) == True
    assert r1.get_event("toto") ==99
    assert r1.get_event("toto") ==None
    assert r1.unsubscribe("toto")


  def test_5(self):
    r1 = Client()
    assert r1.publish("newtoto","hello") == False # nobody is subscribing that
    r2=Client()
    assert r2.subscribe("newtoto") ==True
    assert r1.publish("newtoto","hello") == True
    assert r2.unsubscribe("newtoto") ==True

    assert r2.get_event("newtoto") == None
    assert r1.publish("newtoto","hello") == False # nobody is subscribing that


  def test_6(self):
    r1 = Client()
    assert r1.get_event("xxxxx") == None  # get without subscribe before ....


  def test_7(self):
    r1 = Client()
    assert r1.unsubscribe("xxxxx") == False # unsubscribe without subscribe it before ....


  def test_x(self):
    r1 = Client()
    r2 = Client()
    r3 = Client()
    assert r1.set("yo",666) == True
    assert r2.get("yo") == 666
    assert "yo" in r3.keys()

  def test_events_multi_clients(self):
    r1 = Client()
    r2 = Client()
    rp = Client()
    assert r1.subscribe("mychannel")
    assert r2.subscribe("mychannel")
    assert rp.publish("mychannel","hello")
    assert r1.get_event("mychannel")=="hello"
    assert r1.unsubscribe("mychannel")
    assert r1.get_event("mychannel")==None
    assert r2.get_event("mychannel")=="hello"

  def test_incdec(self):
    r = Client()
    r.delete("val")
    assert r.get("val")==None

    assert r.incr("val")==1
    assert r.get("val")==1

    assert r.incr("val")==2
    assert r.get("val")==2

    assert r.decr("val")==1
    assert r.get("val")==1

    r.delete("val")
    assert r.get("val")==None

    r.decr("val")
    assert r.get("val")==-1

  def test_queue_delete(self):
    r = Client()
    r.delete("ll")
    r.rpush("ll",42)==1
    assert r.get("ll")==[42]
    assert r.delete("ll")
    assert r.get("ll")==None

  def test_set_delete(self):
    r = Client()
    r.delete("ll")
    r.sadd("ll",42)==1
    assert r.get("ll")=={42}
    assert r.delete("ll")
    assert r.get("ll")==None

  def test_queues(self):
    r = Client()
    r.delete("ll")
    assert r.rpush("ll",42)==1
    assert r.rpush("ll",43)==2
    assert r.lpush("ll",41)==3
    assert r.get("ll")==[41,42,43]
    assert r.rpop("ll")==43
    assert r.lpop("ll")==41
    assert r.get("ll")==[42]
    assert r.lpop("ll")==42
    assert r.get("ll")==None
    assert r.lpop("ll")==None
    assert r.rpop("ll")==None


  def test_try_queue_method_with_bad_type(self):
    r = Client()
    r.set("kiki","hello")

    with self.assertRaises(Exception) as context:
       r.rpop("kiki")

    with self.assertRaises(Exception) as context:
       r.rpush("kiki",42)

    assert r.get("kiki")=="hello"



  def test_cache(self):
    r = Client()
    r.setex("kiki",0.05,"hello")
    assert r.get("kiki")=="hello"
    time.sleep(0.5)
    assert r.get("kiki")==None


  def test_cache2(self):
    r = Client()
    r.setex("kiki",0.05,42)
    assert r.incr("kiki",6)==48
    assert r.get("kiki")==48
    time.sleep(0.05)
    assert r.get("kiki")==None



  def test_cache3(self):
    r = Client()
    r.setex("kiki",0.05,42)
    assert r.incr("kiki",6)==48
    assert "kiki" in r.keys()
    time.sleep(0.05)
    assert "kiki" not in r.keys()




  def test_try_incdec_method_with_bad_type(self):
    r = Client()
    r.set("kiki","hello")

    with self.assertRaises(Exception) as context:
       r.incr("kiki")
    with self.assertRaises(Exception) as context:
       r.decr("kiki")

  def test_multi(self):
    r = Client()
    r.set("v1",11)
    r.set("v2",22)
    assert r.get("v1","v3","v2")==[11,None,22]
    assert r.delete("v1","v3","v2")==True
    assert r.get("v1","v3","v2")==[None,None,None]


  def test_try_set_method_with_bad_type(self):
    r = Client()
    r.delete("a_int","unknown")

    assert r.set("a_int",42)
    with self.assertRaises(Exception) as context:
       r.sadd("a_int",42)
    with self.assertRaises(Exception) as context:
       r.srem("a_int",42)

    with self.assertRaises(Exception) as context:
       r.srem("unknown",42)


  def test_set_method(self):
    r = Client()
    r.delete("a_set")

    assert r.sadd("a_set",42)==1
    assert r.sadd("a_set",43)==2
    assert r.sadd("a_set",42)==2

    assert r.get("a_set")==set( (43,42) )

    assert r.srem("a_set",666)==2 # 666 not in set, len is the same

    assert r.srem("a_set",42)==1
    assert r.srem("a_set",42)==1
    assert r.srem("a_set",43)==0


    with self.assertRaises(Exception) as context:
       r.srem("a_set",43)    # the set is dead

    assert r.get("a_set")==None



  def test_cant_mutate_set(self):
    r = Client()
    r.set("jo",{42,43})
    assert r.get("jo")=={42,43}
    with self.assertRaises(Exception) as context:
       r.srem("jo",42)  # jo is a real set, not a redys set

    with self.assertRaises(Exception) as context:
       r.sadd("jo",44)  # jo is a real set, not a redys set


  def test_cant_mutate_queue(self):
    r = Client()
    r.set("jo",[42,43])
    assert r.get("jo")==[42,43]
    with self.assertRaises(Exception) as context:
       r.rpush("jo",44)

    with self.assertRaises(Exception) as context:
       r.lpush("jo",44)

    with self.assertRaises(Exception) as context:
       r.rpop("jo")

    with self.assertRaises(Exception) as context:
       l.rpop("jo")

if __name__=="__main__":
  async def a_spam():
    unittest.main()   # async world

  unittest.main()     # sync world

  loop=asyncio.get_event_loop()
  loop.run_until_complete( a_spam() )
