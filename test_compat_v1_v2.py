import pytest
import asyncio
import redys,time
import multiprocessing

import redys
import redys.v2

from test_sync import server as server1

@pytest.fixture()
def server2():
    s=redys.v2.ServerProcess()
    time.sleep(1)
    yield s
    s.stop()


async def assert_async( bus ):
    assert "pong" == await bus.ping()

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


def assert_sync( bus ):
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

@pytest.mark.asyncio
def test_async1( server1 ):
    assert_sync( redys.Client() )

@pytest.mark.asyncio
async def test_async2( server2 ):
    await assert_async( redys.v2.AClient() )


def test_sync1( server1 ):
    assert_sync( redys.Client() )

def test_sync2( server2 ):
    assert_sync( redys.v2.Client() )


def p1():
    bus=redys.v2.Client()
    bus.subscribe("receptor")

    ll=[]
    while 1:
        event = bus.get_event("receptor")
        if event is not None:
            if event =="end":
                break
            else:
                ll.append(event)

    assert bus.publish("result",ll)

def p2():
    with redys.v2.Client() as bus:  # <- test with/context (like v1)
        for i in range(10):
            assert bus.publish("receptor",i)
        assert bus.publish("receptor","end")

def test_events2( server2 ):
    bus=redys.v2.Client()

    pid1=multiprocessing.Process(target=p1)
    pid1.start()
    pid2=multiprocessing.Process(target=p2)
    pid2.start()

    bus.subscribe("result")

    while 1:
        event = bus.get_event("result")
        if event:
            assert event==[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
            break

    pid1.terminate()
    pid2.terminate()


