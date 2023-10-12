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
logger = logging.getLogger(__name__)

import multiprocessing,threading,time
from concurrent.futures import ThreadPoolExecutor

class ServOne:
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
                name=question[:10]

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
            #-------------------------------------
            # just for compatibility with original
            # (there is no real context needs)
            #-------------------------------------
            def __enter__(self):
                return self
            def __exit__(self,*args):
                pass
            #-------------------------------------
        return ProxySync()

    @property
    def clientasync(self):
        class ProxyASync:
            def __getattr__(this,name:str):
                async def _(*a,**k):
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
            #-------------------------------------
            # just for compatibility with original
            # (there is no real context needs)
            #-------------------------------------
            def __enter__(self):
                return self
            def __exit__(self,*args):
                pass
            #-------------------------------------
        return ProxyASync()
