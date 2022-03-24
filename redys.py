#!/usr/bin/python3
# -*- coding: utf-8 -*-
import asyncio,pickle,uuid,inspect,time

__version__="0.9.7"

##############################################################################
## Client Code
##############################################################################
from concurrent.futures import ThreadPoolExecutor

sideloop = asyncio.new_event_loop()

def async2sync(coro):
    with ThreadPoolExecutor(max_workers=1) as exe:
        r=exe.submit(sideloop.run_until_complete, coro )
        return r.result()

async def readall( reader ):
    CHUNK_LIMIT=8192
    response = b''
    while True:
        chunk = await reader.read(CHUNK_LIMIT)
        if chunk:
            response += chunk
            if len(chunk) < CHUNK_LIMIT:
                break
        else:
            break
    return response

class Client:
    asynk=False
    def __init__(self,address:tuple=("localhost",13475)):
        self.address=address
        self.reader=None
        self.writer=None
        self.id=uuid.uuid4().hex
        r=OpClient("for intropspection only")
        self._methods={n:inspect.signature(getattr(r,n)) for n in dir(r) if callable(getattr(r, n)) and not n.startswith("_")}

    def __getattr__(self,name): # expose methods of OpClient
        if name in self._methods:
            ## ASYNC VERSION
            async def asyncCall(*a,**k):
                ba=self._methods[name].bind(*a,**k)
                return await self._com( dict(command=name,args=ba.args,kwargs=ba.kwargs) )

            ## SYNC VERSION
            def syncCall(*a,**k):
                ba=self._methods[name].bind(*a,**k)
                return async2sync( self._com( dict(command=name,args=ba.args,kwargs=ba.kwargs) ) )

            return asyncCall if self.asynk else syncCall
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

        data = await readall(self.reader)
        obj=pickle.loads(data)
        if type(obj)==Exception: raise obj
        return obj

    def close(self):
        try:
            self.writer.close()
            if not asynk:
                async2sync( self.writer.wait_closed() )
        except:
            pass

class AClient(Client):
    asynk=True



##############################################################################
## Common Code
##############################################################################
db={}
events={}
watchs=[]   # watch ttl
class OpClient: # exposed redys's methods (https://redis.io/commands#generic)
    def __init__(self,id:str):
        self.id=id

    def __call__(self,obj):
        try:
            return getattr(self, obj["command"])(*obj["args"],**obj["kwargs"])
        except Exception as e:
            return Exception(str(e))

    def ping(self):
        return "pong"

    #cache
    #--------------------------------------------
    def setex(self,key:str,ttl:int,value): #useless since ttl is available in set()
        db[key]=(value,time.time()+ttl if ttl else None)
        if not( key in watchs): watchs.append( key )
        return True

    #classics
    #--------------------------------------------
    def set(self,key:str,value,ttl:int=None):
        return self.setex(key,ttl,value)

    def _get(self,key:str):
        t=db.get(key,(None,None))
        if type(t)==tuple:
            value,ttl=t
            if ttl is None:
                return value
            elif time.time() <= ttl:
                return value
            else:
                del db[key]
                return None
        elif type(t)==set:
            return t
        elif type(t)==list:
            return t

    def get(self,*keys):
        l=[self._get(k) for k in keys]
        return l[0] if len(l)==1 else l

    def delete(self,*keys):
        for key in keys:
            if key in db: del db[key]
        return True

    def keys(self):
        return list([k for k in list(db.keys()) if self._get(k)!=None])

    def _inc(self,key:str,offset):
        value,ttl=db.get(key,(0,None))
        value+=offset
        db[key]=(value,ttl)
        return value

    def incr(self,key,offset=1):
        return self._inc(key,offset)
    def decr(self,key,offset=-1):
        return self._inc(key,offset)

    #sets
    #--------------------------------------------
    def _modset(self,key:str,add=None,rem=None):
        s=db.get(key,set())
        if type(s)!=set: raise Exception("key '%s' is not a set"%key)
        if add: s.add( add )
        if rem and rem in s:
            s.remove(rem)
        if s:
            db[key]=s
            return len(s)
        else:
            if key in db:
                del db[key]
                return len(s)
            else:
                raise Exception(Exception("key '%s' is not a set"%key))

    def sadd(self,key:str,obj):
        return self._modset(key,add=obj)

    def srem(self,key:str,obj):
        return self._modset(key,rem=obj)

    #queues
    #--------------------------------------------
    def _modpush(self,key:str,obj,idx):
        l=db.get(key,[])
        if type(l)!=list: raise Exception("key '%s' is not a queue"%key)
        if idx==-1:
            l.append(obj)
        else:
            l.insert(idx,obj)
        db[key]=l
        return len(l)

    def rpush(self,key:str,obj):
        return self._modpush(key,obj,-1)
    def lpush(self,key:str,obj):
        return self._modpush(key,obj,0)

    def _modpop(self,key:str,idx):
        l=db.get(key,[])
        if type(l)!=list: raise Exception("key '%s' is not a queue"%key)
        if len(l)>0:
            r=l.pop(idx)
            if l:
                db[key]=l
            else:
                del db[key]
            return r

    def lpop(self,key:str):
        return self._modpop(key,0)
    def rpop(self,key:str):
        return self._modpop(key,-1)

    # events (in own space)
    #--------------------------------------------
    def subscribe(self,event:str):
        events.setdefault(event,{}).setdefault(self.id,[])
        return True
    def unsubscribe(self,event:str):
        if event in events:
            if self.id in events[event]:
                del events[event][self.id]
                if len(events[event])==0:
                    del events[event]
                return True
        return False
    def publish(self,event:str,obj):
        if event in events:
            for i in events[event]:
                events[event][i].append(obj)
            return True
        return False
    def get_event(self,event:str):
        if event in events:
            if self.id in events[event]:
                if len(events[event][self.id])>0:
                    return events[event][self.id].pop(0)
        return None

##############################################################################
## Server Code
##############################################################################
async def watcher(): # watch key with ttl, to remove them automatically
    while 1:
        await asyncio.sleep(1)
        for key in []+watchs:
            r=OpClient( "for ttl watcher" ).get(key)
            if r is None:
                watchs.remove(key)


async def redys_handler(reader, writer):
    asyncio.ensure_future(watcher())
    try:
        client=None
        while 1:
            input = pickle.loads(await readall(reader))

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


async def Server( address:tuple =("localhost",13475) ):
    server = await asyncio.start_server(redys_handler, address[0], address[1])
    await server.wait_closed()


if __name__=="__main__":
    loop=asyncio.get_event_loop()
    loop.run_until_complete( Server() )
