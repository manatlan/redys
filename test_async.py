import pytest
import asyncio
import redys
import subprocess

from test_sync import server


@pytest.mark.asyncio
async def test_ping( server ):
    with redys.AClient() as bus:
        x = await bus.ping()
        assert x == "pong"

@pytest.mark.asyncio
async def test_kill( server ):
    with redys.AClient() as bus:
        x = await bus.KILL()
        assert x is True



@pytest.mark.asyncio
async def test_asyncTests( server ):
    r=redys.AClient()
    assert await r.set("v",12)
    assert await r.incr("v")==13
    assert await r.incr("v",8)==21
    assert await r.decr("v")==20
    assert await r.get("v")==20
    assert await r.delete("v")==True
    assert await r.get("v","fdsfsdfd")==[None,None]
    assert await r.sadd("v","a")==1
    assert await r.sadd("v","b")==2
    assert await r.sadd("v","b")==2
    assert await r.get("v")=={"a","b"}
    assert await r.srem("v","c")==2
    assert await r.srem("v","b")==1
    assert await r.srem("v","a")==0
    assert await r.get("v")==None
    assert await r.rpush("v","2")==1
    assert await r.rpush("v",3)==2
    assert await r.lpush("v","1")==3
    assert await r.get("v")==["1","2",3]
    assert await r.lpop("v")=="1"
    assert await r.rpop("v")==3
    assert await r.get("v")==["2"]
    assert await r.delete("v")==True
    assert "v" not in await r.keys()

if __name__=="__main__":

    asyncio.run(test_kill("x"))