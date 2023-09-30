import pytest
import asyncio
import redys

@pytest.fixture()
def server():
    print("tearup")
    asyncio.ensure_future( redys.Server() )
    yield "resource"
    print("teardown")

async def test_fun( server ):
    with redys.AClient() as bus:
        await bus.set("val",42)
        x = await bus.get("val")
        assert x == 42