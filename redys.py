import asyncio,pickle,uuid

MAX=100000000
db={}
events={}

##############################################################################
## Client Code
##############################################################################
class Client:
    def __init__(self,address=("localhost",13475)):
        assert type(address)==tuple
        self.address=address
        self.reader=None
        self.writer=None
        self.id=uuid.uuid4().hex

    def __enter__(self):
        return self
    def __exit__(self,*args):
        self.close()
    def __del__(self):
        self.close()

    async def _com(self,obj):
        if self.reader==None and self.writer==None: # not connected ... so connect !
            self.reader, self.writer = await asyncio.open_connection( self.address[0],self.address[1])
            await self._com( dict(command="init",id=self.id) )

        self.writer.write(pickle.dumps(obj))
        await self.writer.drain()

        data = await self.reader.read(MAX)
        return pickle.loads(data)

    def close(self):
        self.writer.close()

    async def set(self,key,value):
        return await self._com( dict(command="set",key=key,value=value) )
    async def get(self,*key):
        return await self._com( dict(command="get",keys=key))
    async def delete(self,*key):
        return await self._com( dict(command="del",keys=key))
    async def keys(self):
        return await self._com( dict(command="keys"))

    async def register(self,event):
        return await self._com( dict(command="register",event=event) )
    async def unregister(self,event):
        return await self._com( dict(command="unregister",event=event) )

    async def subscribe(self,event):
        return await self._com( dict(command="subscribe",event=event) )

    async def publish(self,event,obj):
        return await self._com( dict(command="publish",event=event,obj=obj) )


##############################################################################
## Server Code
##############################################################################
async def redys_handler(reader, writer):
    id=None

    def protocol( obj ):
        global id
        if obj["command"]=="init":
            id=obj["id"]
            return True
        else:
            if id:
                if obj["command"]=="set":
                    k,v=obj["key"],obj["value"]
                    db[k]=v
                    return True
                elif obj["command"]=="get":
                    keys=obj["keys"]
                    ll=[db.get(k,None) for k in keys]
                    v = ll[0] if len(ll)==1 else ll
                    return v
                elif obj["command"]=="del":
                    keys=obj["keys"]
                    for i in keys:
                        if i in db: del db[i]
                    return True
                elif obj["command"]=="keys":
                    l=list(db.keys())
                    return l

                elif obj["command"]=="register":
                    event=obj["event"]
                    events.setdefault(event,{}).setdefault(id,[])
                    return True

                elif obj["command"]=="unregister":
                    event=obj["event"]
                    if event in events:
                        if id in events[event]:
                            del events[event][id]
                            del events[event]
                            return True
                    return False # unkown registration (id or event)

                elif obj["command"]=="publish":
                    event,msg=obj["event"],obj["obj"]
                    if event in events:
                        for id in events[event]:
                            events[event][id].append(msg)
                        return True
                    return False   # nobody has registered that

                elif obj["command"]=="subscribe":
                    event=obj["event"]
                    if event in events:
                        if id in events[event]:
                            if len(events[event][id])>0:
                                return events[event][id].pop(0)
                    return None  # empty queue or unknonw event

    try:
        while 1:
            print(":"*80)
            print("::",id)
            print("::",db)
            print("::",events)
            print(":"*80)
            data = await reader.read(MAX)
            input = pickle.loads(data)
            addr = writer.get_extra_info('peername')

            output=protocol(input)
            #~ print(input,"--->",output)

            writer.write( pickle.dumps(output) )
            await writer.drain()

    except EOFError:
        pass
    finally:

        #~ events_to_remove=[]
        #~ for event in events:
            #~ if id in events[event]:
                #~ del events[event][id]
                #~ if len(events[event])==0:
                    #~ events_to_remove.append(event)
        #~ for event in events_to_remove:
            #~ del events[event]
        writer.close()

async def Server( address=("localhost",13475) ):
    assert type(address)==tuple
    server = await asyncio.start_server(redys_handler, address[0], address[1])

    async with server:
        await server.serve_forever()



if __name__=="__main__":

    async def other():
        while 1:
            await asyncio.sleep(0.5)
            print("alive")

    async def main():
        await asyncio.gather(
            other(),Server()
        )

    asyncio.run(main())
