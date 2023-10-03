import asyncio
import redys.v2, time
import multiprocessing


async def myserver():
    print("server started")
    await asyncio.sleep(5)
    print("server end")

def process():
    asyncio.run( redys.v2.loop( myserver() ) )

if __name__=="__main__":
    multiprocessing.Process(target=process).start()
    multiprocessing.Process(target=process).start()
    multiprocessing.Process(target=process).start()

    import time
    time.sleep(5)

