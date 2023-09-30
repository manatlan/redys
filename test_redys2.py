import pytest
import asyncio
import redys
import subprocess

from redys.redys2 import Redys2
from redys.usot import Usot


@pytest.mark.asyncio
async def test_bato( ):
    r=Usot(Redys2,port=19999)
    r.start()

    bus=r.clientasync
    assert "pong" == await bus.ping()

    assert None == await bus.get("a")

    await bus.set("a","kkkkkkkkkkkk"*10_000_000)    # grand max

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

    r.stop()
