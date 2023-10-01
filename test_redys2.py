import pytest
import asyncio
import redys,time
import multiprocessing

from redys.v2 import ServerProcess,AClient,Client


@pytest.fixture()
def server():
    s=ServerProcess()
    time.sleep(1)
    yield s
    s.stop()


@pytest.mark.asyncio
async def test_async2( server ):
    bus=AClient()
    assert "pong" == await bus.ping()

    assert None == await bus.get("a")

    # await bus.set("a","kkkkkkkkkkkk"*10_000_000)    # grand max

    assert await bus.set("v",12)
    assert await bus.incr("v")==13
    assert await bus.incr("v",8)==21
    assert await bus.decr("v")==20
    assert await bus.get("v")==20
    assert await bus.delete("v")==True
    assert await bus.get("v","fdsfsdfd")==[None,None]
    assert await bus.sadd("v","a")==1
    assert await bus.sadd("v","b")==2
    assert await bus.sadd("v","b")==2
    assert await bus.get("v")=={"a","b"}
    assert await bus.srem("v","c")==2
    assert await bus.srem("v","b")==1
    assert await bus.srem("v","a")==0
    assert await bus.get("v")==None
    assert await bus.rpush("v","2")==1
    assert await bus.rpush("v",3)==2
    assert await bus.lpush("v","1")==3
    assert await bus.get("v")==["1","2",3]
    assert await bus.lpop("v")=="1"
    assert await bus.rpop("v")==3
    assert await bus.get("v")==["2"]
    assert await bus.delete("v")==True



def test_sync( server ):
    bus=Client()
    assert "pong" == bus.ping()

    assert bus.set("v",12)
    assert bus.incr("v")==13
    assert bus.incr("v",8)==21
    assert bus.decr("v")==20
    assert bus.get("v")==20
    assert bus.delete("v")==True
    assert bus.get("v","fdsfsdfd")==[None,None]
    assert bus.sadd("v","a")==1
    assert bus.sadd("v","b")==2
    assert bus.sadd("v","b")==2
    assert bus.get("v")=={"a","b"}
    assert bus.srem("v","c")==2
    assert bus.srem("v","b")==1
    assert bus.srem("v","a")==0
    assert bus.get("v")==None
    assert bus.rpush("v","2")==1
    assert bus.rpush("v",3)==2
    assert bus.lpush("v","1")==3
    assert bus.get("v")==["1","2",3]
    assert bus.lpop("v")=="1"
    assert bus.rpop("v")==3
    assert bus.get("v")==["2"]
    assert bus.delete("v")==True

# def p1():
#     bus=Client()
#     bus.subscribe("receptor")

#     ll=[]
#     while 1:
#         event = bus.get_event("receptor")
#         if event is not None:
#             if event =="end":
#                 break
#             ll.append(event)

# def p2():
#     bus=Client()
#     for i in range(100):
#         assert bus.publish("receptor",i)
#     assert bus.publish("receptor","end")

# def test_events( server ):
#     multiprocessing.Process(p1).start()
#     multiprocessing.Process(p2).start()
