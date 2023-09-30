import pytest
import asyncio
import redys

@pytest.fixture()
def server():
    print("tearup")
    asyncio.ensure_future( redys.Server() )
    yield "resource"
    print("teardown")

@pytest.mark.asyncio
async def test_ping( server ):
    with redys.AClient() as bus:
        x = await bus.ping()
        assert x == "pong"

@pytest.mark.asyncio
async def test_get_set( server ):
    with redys.AClient() as bus:
        x = await bus.get("val")
        assert x is None

        assert await bus.set("val",42)

        x = await bus.get("val")
        assert x == 42

        o=dict(a=42,s="hello",pi=3.14)
        assert await bus.set("val",o)

        x = await bus.get("val")
        assert x == o
