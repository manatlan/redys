
import multiprocessing.connection
import asyncio,os,uuid,time,_thread,threading,atexit
from pprint import pprint

db={}           # <- the in-memory db (a dict)
events={}       # <- to handle the pub/sub mechanism


class Client:
    def __init__(self,address="/tmp/redys.socket",authkey="redys"):
        if type(authkey)==str: authkey=authkey.encode()
        self.id=uuid.uuid4().hex
        self._x=multiprocessing.connection.Client(address,authkey=authkey)
        assert self._com( dict(command="init",id=self.id) )

    def __enter__(self):
        return self
    def __exit__(self,*args):
        self.close()

    def _com(self,obj):
        self._x.send( obj )
        return self._x.recv()
    def close(self):
        self._x.close()

    def set(self,key,value):
        return self._com( dict(command="set",key=key,value=value) )
    def get(self,*key):
        return self._com( dict(command="get",keys=key))
    def delete(self,*key):
        return self._com( dict(command="del",keys=key))
    def keys(self):
        return self._com( dict(command="keys"))

    def register(self,event):
        return self._com( dict(command="register",event=event) )
    def unregister(self,event):
        return self._com( dict(command="unregister",event=event) )

    def subscribe(self,event):
        return self._com( dict(command="subscribe",event=event) )

    def publish(self,event,obj):
        return self._com( dict(command="publish",event=event,obj=obj) )

async def Server(address="/tmp/redys.socket",authkey="redys"):
    lock = threading.Lock()

    def on_new_client(conn):
        try:
            id=None
            while True:
                #~ with lock:
                    #~ print("Client:",id)
                    #~ print(db)
                    #~ pprint(events)

                obj=conn.recv()

                if obj["command"]=="init":
                    id=obj["id"]
                    conn.send( True )
                else:
                    if id:
                        if obj["command"]=="set":
                            k,v=obj["key"],obj["value"]
                            with lock:
                                db[k]=v
                            conn.send( True )
                        elif obj["command"]=="get":
                            keys=obj["keys"]
                            with lock:
                                ll=[db.get(k,None) for k in keys]
                            v = ll[0] if len(ll)==1 else ll
                            conn.send( v)
                        elif obj["command"]=="del":
                            keys=obj["keys"]
                            with lock:
                                for i in keys:
                                    if i in db: del db[i]
                            conn.send( True )
                        elif obj["command"]=="keys":
                            with lock:
                                l=list(db.keys())
                            conn.send( l )

                        elif obj["command"]=="register":
                            event=obj["event"]
                            with lock:
                                events.setdefault(event,{}).setdefault(id,[])
                            conn.send( True )

                        elif obj["command"]=="unregister":
                            event=obj["event"]
                            with lock:
                                if event in events:
                                    if id in events[event]:
                                        del events[event][id]
                                        del events[event]
                                        conn.send( True )
                                        continue
                            conn.send( False ) # unkown registration (id or event)

                        elif obj["command"]=="publish":
                            event,msg=obj["event"],obj["obj"]
                            with lock:
                                if event in events:
                                    for id in events[event]:
                                        events[event][id].append(msg)
                                    conn.send( True )
                                    continue
                            conn.send( False )  # nobody has registered that

                        elif obj["command"]=="subscribe":
                            event=obj["event"]
                            with lock:
                                if event in events:
                                    if id in events[event]:
                                        if len(events[event][id])>0:
                                            conn.send( events[event][id].pop(0) )
                                            continue
                            conn.send( None ) # empty queue or unknonw event
        except EOFError:
            pass
        finally:
            with lock:
                events_to_remove=[]
                for event in events:
                    if id in events[event]:
                        del events[event][id]
                        if len(events[event])==0:
                            events_to_remove.append(event)
                for event in events_to_remove:
                    del events[event]
            conn.close()

    if type(address)==str:
        try:
            os.unlink(address)
        except OSError:
            if os.path.exists(address):
                raise
    if type(authkey)==str: authkey=authkey.encode()

    with multiprocessing.connection.Listener(address, authkey=authkey) as listener:
        while 1:
            conn=listener.accept()
            _thread.start_new_thread(on_new_client,(conn,))



if __name__=="__main__":
    asyncio.run( Server() )
