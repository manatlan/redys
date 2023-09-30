import pytest
import asyncio
import redys

@pytest.fixture()
def server():
    print("tearup")
    asyncio.ensure_future( redys.Server() )
    yield "resource"
    print("teardown")

def test_ping( server ):
    with redys.Client() as bus:
        x = bus.ping()
        assert x == "pong"
