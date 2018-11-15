import asyncio,pickle,uuid,inspect

MAX=100000000

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
        r=OpClient("for exploration only")
        self._methods={n:inspect.getargspec(getattr(r,n)).args[1:] for n in dir(r) if callable(getattr(r, n)) and not n.startswith("_")}

    def __getattr__(self,name): # expose methods of OpClient
        if name in self._methods:
            async def _(*a): # no kargs !!!
                obj=dict(zip( self._methods[name],a ))
                obj["command"]=name
                return await self._com( obj )
            return _
        else:
            raise AttributeError("%r object has no attribute %r" % (self.__class__, name))

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
        if self.writer:
            self.writer.close()



##############################################################################
## Server Code
##############################################################################
db={}
events={}


class OpClient: # exposed redys's methods
    def __init__(self,id):
        self.id=id

    def __call__(self,obj):
        method=obj["command"]
        del obj["command"]
        return getattr(self,method)(**obj)

    def set(self,key,value):
        db[key]=value
        return True
    def get(self,key):
        return db.get(key,None)
    def delete(self,key):
        if key in db: del db[key]
        return True
    def keys(self):
        return list(db.keys())
    def incr(self,key):
        db[key]=db.get(key,0)+1
        return True
    def decr(self,key):
        db[key]=db.get(key,0)-1
        return True
    def subscribe(self,event):
        events.setdefault(event,{}).setdefault(self.id,[])
        return True
    def unsubscribe(self,event):
        if event in events:
            if self.id in events[event]:
                del events[event][self.id]
                if len(events[event])==0:
                    del events[event]
                return True
        return False
    def publish(self,event,obj):
        if event in events:
            for i in events[event]:
                events[event][i].append(obj)
            return True
        return False
    def get_event(self,event):
        if event in events:
            if self.id in events[event]:
                if len(events[event][self.id])>0:
                    return events[event][self.id].pop(0)
        return None

async def redys_handler(reader, writer):
    try:
        client=None
        while 1:
            data = await reader.read(MAX)
            input = pickle.loads(data)
            addr = writer.get_extra_info('peername')

            if client is None:
                if input["command"]=="init":
                    client=OpClient(input["id"])
                    output=True
                else:
                    output=None
            else:
                 output = client( input )

            writer.write( pickle.dumps(output) )
            await writer.drain()

    except EOFError:
        pass
    finally:
        for event in list(events.keys()):
            client.unsubscribe(event)
        writer.close()

async def Server( address=("localhost",13475) ):
    assert type(address)==tuple
    server = await asyncio.start_server(redys_handler, address[0], address[1])
    await server.wait_closed()


if __name__=="__main__":

    #~ async def other():
        #~ while 1:
            #~ await asyncio.sleep(0.5)
            #~ print("alive")

    #~ async def main():
        #~ await asyncio.gather(
            #~ other(),Server()
        #~ )

    asyncio.run( Server())
