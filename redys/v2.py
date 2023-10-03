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

from .servone import ServOne

class Redys2:
    def __init__(self):
        self.dico={}
        self.watchs=[]
        self.events={}
        self.id="XXXXXXXXXXXXXX"    #TODO: really sense ?

    # #TODO: add task on this
    # async def watcher(self): # watch key with ttl, to remove them automatically
    #     while self.watchs is not None:
    #         await asyncio.sleep(1)
    #         for key in self.watchs:
    #             r=self.get(key)
    #             if r is None:
    #                 self.remove(key)


    def ping(self):
        return "pong"

    # TODO: really got sense ???
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

REDYS2=ServOne(Redys2,port=23475)

def Server():
    """ run server in current loop """
    REDYS2.start()
    return REDYS2

def ServerProcess():
    """ run server in a process loop """
    REDYS2.start_process()
    return REDYS2

def AClient():
    return REDYS2.clientasync

def Client():
    return REDYS2.clientsync

async def loop(coro):
    """ run a redys server, and wait for the loop 'coro'
        ensure only one process server/redys+loop
    """
    REDYS2.start()
    try:
        while not REDYS2._task.done():
            await asyncio.sleep(0.1)

        if REDYS2._task.exception() is None:
            print("<> Run redys loop")
            await coro
        else:
            print("<> Redys loop is already running ! abort !")
    finally:
        REDYS2.stop()