# -*- coding: utf-8 -*-
# #############################################################################
# Copyright (C) 2023 manatlan manatlan[at]gmail(dot)com
#
# MIT licence
#
# https://github.com/manatlan/htagweb
# #############################################################################
import asyncio,sys
import logging,pickle
from typing import Callable

from regex import R
logger = logging.getLogger(__name__)

class SessionMemory:
    def __init__(self):
        self.SESSIONS={}
    def get(self,uid:str):
        return self.SESSIONS.get(uid,{})
    def set(self,uid:str,value:dict):
        assert isinstance(value,dict)
        self.SESSIONS[uid]=value



import multiprocessing,threading,time
from concurrent.futures import ThreadPoolExecutor

class Usot:
    """ Unique Source Of Truth
        Helper to create server and client for a RPC
    """
    def __init__(self,klass:Callable,host:str="127.0.0.1",port:int=17788):
        self._klass=klass
        self._host=host
        self._port=int(port)

        self._task=None
        self._p=None

    def start(self):
        """ start an async task in the current loop, which spawn a tcp server
            wich will expose methods of the 'klass' on 'host:port'
        """
        def task():
            ###########################################################################
            instance = self._klass()

            ###########################################################################
            async def serve(reader, writer):

                question = await reader.read()

                #~ logger.debug("Received from %s, size: %s",writer.get_extra_info('peername'),len(question))

                trunc = lambda x,limit=100: str(x)[:limit-3]+"..." if len(str(x))>limit else str(x)
                fmt=lambda a,k: f"""{trunc(a)[1:-1]}{','.join([f"{k}={trunc(v)}" for k,v in k.items()])}"""



                try:
                    name,a,k = pickle.loads(question)
                    method = getattr(instance, name)
                    logger.debug(">>> %s.%s( %s )", instance.__class__.__name__,name, fmt(a,k))
                    if asyncio.iscoroutinefunction(method):
                        reponse = await method(*a,**k)
                    else:
                        reponse = method(*a,**k)
                        logger.debug("<<< %s", trunc(reponse))
                except Exception as e:
                    logger.error("Error calling %s(...) : %s" % (name,e))
                    reponse=e

                data=pickle.dumps(reponse)
                #~ logger.debug("Send size: %s",len(data))
                writer.write(data)
                await writer.drain()
                writer.write_eof()

                writer.close()
                await writer.wait_closed()

            ###########################################################################

            return asyncio.start_server( serve, self._host, self._port)

        def callback(task):
            try:
                error=task.exception()
            except asyncio.exceptions.CancelledError as e:
                error=e
            if not error:
                logger.info("Usot: %s started on %s:%s !",self._klass.__name__,self._host,self._port)
            elif isinstance(error,OSError):
                logger.warning("Usot: %s exists on %s:%s !",self._klass.__name__,self._host,self._port)
            elif isinstance(error, asyncio.exceptions.CancelledError):
                logger.warning("Usot: %s cancelled !",self._klass.__name__)
            else:
                raise error

        self._task= asyncio.create_task( task() )
        self._task.add_done_callback(callback)

    def _instanciate(self):
        self._running=True
        async def loop():
            self.start()
            while self._running:
                await asyncio.sleep(0.1)
        #run its own loop
        asyncio.run(loop())

    def start_process(self):
        ''' start a process, with own loop to run the task ^^ '''
        self._p=multiprocessing.Process(target=self._instanciate)
        self._p.start()

    def start_thread(self):
        ''' start a thread, with own loop to run the task ^^ '''
        self._p=threading.Thread(target=self._instanciate)
        self._p.start()

    def stop(self):
        ''' will try to stop the server '''
        logger.info("try to stop server")
        if self._task: self._task.cancel()
        self._running=False # stop the loop in process/thread
        if self._p:
            if isinstance(self._p, multiprocessing.Process):
                self._p.terminate() # process mode
            self._p.join()


    @property
    def clientsync(self):
        class ProxySync:
            def __getattr__(this,name:str):
                def _(*a,**k):
                    am=self.clientasync.__getattr__(name)
                    coro = am(*a,**k)

                    sideloop=asyncio.new_event_loop()
                    with ThreadPoolExecutor(max_workers=1) as exe:
                        r=exe.submit(sideloop.run_until_complete, coro )
                        retour= r.result()
                    sideloop.close()
                    return retour
                return _
        return ProxySync()

    @property
    def clientasync(self):
        class ProxyASync:
            def __getattr__(this,name:str):
                async def _(*a,**k):
                    try: # ensure server was started
                        await self._task
                    except:
                        pass

                    reader, writer = await asyncio.open_connection(self._host,self._port)
                    question = pickle.dumps( (name,a,k) )
                    # logger.debug('Sending data of size: %s',len(question))
                    writer.write(question)
                    await writer.drain()
                    writer.write_eof()
                    data = await reader.read()
                    # logger.debug('recept data of size: %s',len(data))
                    reponse = pickle.loads( data )
                    writer.close()
                    await writer.wait_closed()
                    if isinstance(reponse,Exception):
                        raise reponse
                    else:
                        return reponse
                return _

        return ProxyASync()


class Redys2:
    def __init__(self):
        self.dico={}
        self.watchs=[]
        self.events={}
        self.id="XXXXXXXXXXXXXX"

    def ping(self):
        return "pong"

    # def KILL(self):
    #     return True


    #cache
    #--------------------------------------------
    def setex(self,key:str,ttl:int,value): #useless since ttl is available in set()
        self.dico[key]=(value,time.time()+ttl if ttl else None)
        if not( key in self.watchs): self.watchs.append( key )
        return True

    #classics
    #--------------------------------------------
    def set(self,key:str,value,ttl:int=None):
        return self.setex(key,ttl,value)

    def _get(self,key:str):
        t=self.dico.get(key,(None,None))
        if type(t)==tuple:
            value,ttl=t
            if ttl is None:
                return value
            elif time.time() <= ttl:
                return value
            else:
                del self.dico[key]
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
            if key in self.dico: del self.dico[key]
        return True

    def keys(self):
        return list([k for k in list(self.dico.keys()) if self._get(k)!=None])

    def _inc(self,key:str,offset):
        value,ttl=self.dico.get(key,(0,None))
        value+=offset
        self.dico[key]=(value,ttl)
        return value

    def incr(self,key,offset=1):
        return self._inc(key,offset)
    def decr(self,key,offset=-1):
        return self._inc(key,offset)

    #sets
    #--------------------------------------------
    def _modset(self,key:str,add=None,rem=None):
        s=self.dico.get(key,set())
        if type(s)!=set: raise Exception("key '%s' is not a set"%key)
        if add: s.add( add )
        if rem and rem in s:
            s.remove(rem)
        if s:
            self.dico[key]=s
            return len(s)
        else:
            if key in self.dico:
                del self.dico[key]
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
        l=self.dico.get(key,[])
        if type(l)!=list: raise Exception("key '%s' is not a queue"%key)
        if idx==-1:
            l.append(obj)
        else:
            l.insert(idx,obj)
        self.dico[key]=l
        return len(l)

    def rpush(self,key:str,obj):
        return self._modpush(key,obj,-1)
    def lpush(self,key:str,obj):
        return self._modpush(key,obj,0)

    def _modpop(self,key:str,idx):
        l=self.dico.get(key,[])
        if type(l)!=list: raise Exception("key '%s' is not a queue"%key)
        if len(l)>0:
            r=l.pop(idx)
            if l:
                self.dico[key]=l
            else:
                del self.dico[key]
            return r

    def lpop(self,key:str):
        return self._modpop(key,0)
    def rpop(self,key:str):
        return self._modpop(key,-1)

    # events (in own space)
    #--------------------------------------------
    def subscribe(self,event:str):
        self.events.setdefault(event,{}).setdefault(self.id,[])
        return True
    def unsubscribe(self,event:str):
        if event in self.events:
            if self.id in self.events[event]:
                del self.events[event][self.id]
                if len(self.events[event])==0:
                    del self.events[event]
                return True
        return False
    def publish(self,event:str,obj):
        if event in self.events:
            for i in self.events[event]:
                self.events[event][i].append(obj)
            return True
        return False
    def get_event(self,event:str):
        if event in self.events:
            if self.id in self.events[event]:
                if len(self.events[event][self.id])>0:
                    return self.events[event][self.id].pop(0)
        return None

if __name__=="__main__":
    import pytest
    import logging,multiprocessing,threading
    logging.basicConfig(format='[%(levelname)-5s] %(name)s: %(message)s',level=logging.DEBUG)

    async def t():
        r=Usot(Redys2,port=19999)
        r.start()

        bus=r.clientasync
        assert "pong" == await bus.ping()

        assert None == await bus.get("a")

        await bus.set("a","kkkkkkkkkkkk"*1_000_000)

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

    asyncio.run(t())