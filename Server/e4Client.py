from concurrent.futures import thread
import time
import asyncio
import socket
from queue import Queue
import threading
from enum import Enum

class ResponseItem:
    def __init__(self):
        self.response = None
        self.lock = asyncio.Event()
        self.caller_loop = asyncio.get_event_loop()
    
    async def wait_for_response(self):
        await self.lock.wait()
        return self.response
    
    def set_response(self, response):
        self.response = response
        self.caller_loop.call_soon_threadsafe(self.lock.set)

class E4Handler:
    def __init__(self, conn_lost_f):
        self.reader = None
        self.writer = None
        self.running = False
        self.read_task = None
        self._conn_lost_f = conn_lost_f
        self._resp_dict = {}
        self._callback = {}
    
    def __del__(self):
        if self.writer is not None:
            self.writer.close()

    async def start(self, port=28000, event=None):
        if not self.running and self.read_task is None:
            self.running = True
            self.port = port
            self.event = event
            self.read_task = asyncio.create_task(self._start_handler())
        elif event is not None:
            event.set()

    def ensure_connection(self):
        try:
            self.read_task.result()
        except OSError:
            return False
        except asyncio.exceptions.InvalidStateError:
            return True
        return True

    async def _start_handler(self):
        try:
            self.reader, self.writer = await asyncio.open_connection("127.0.0.1", self.port)
        except OSError as e:
            self.running = False
            if self.event is not None:
                self.event.set()
            raise
        await self._stream_reader()
        #await read_task

    async def exit(self):
        if self.running:
            self.running = False
            # Other stuff
            self.writer.close()
            await self.read_task
            self.read_task = None
            self._resp_dict = {}

    
    async def send(self, cmd, message=""):
        if self.writer is None:
            raise Exception("Connection is not yet established.")
        send_msg = f"{cmd} {message}\r\n"
        self.writer.write(send_msg.encode())
        await self.writer.drain()
        return await self._response(cmd)

    def callback(self, cmd, func):
        self._callback[cmd] = func


    async def _response(self, resp):
        self._resp_dict[resp] = ResponseItem()
        return await self._resp_dict[resp].wait_for_response()

    async def _stream_reader(self):
        reading = True
        if self.event is not None:
            self.event.set()
        while reading:
            try:
                raw_msg = await self.reader.readuntil(b'\n')
                msg = raw_msg.decode()[:-1]
                await self._handle_cmd(msg)
            except asyncio.exceptions.IncompleteReadError:
                reading = False
    
    async def _handle_cmd(self, msg):
        cmd = msg.split(' ')
        if msg == "Unknown command":
            return None
        if cmd[0] == "R":
            await self._server_response(msg)
        elif cmd[0][:2] == "E4":
            if cmd[0] in self._callback:
                timestamp = float(cmd[1].replace(",","."))
                data = [float(cmd[i].replace(",",".")) for i in range(2, len(cmd))]
                self._callback[cmd[0]](timestamp, data)

    def set_dc_callback(self, func):
        self._conn_lost_f = func

    async def _server_response(self, msg):
        msg_lst = msg.split(' ')
        cmd = msg_lst[1]
        if cmd in self._resp_dict:
            self._resp_dict[cmd].set_response(msg)
        elif cmd == 'connection':
            if msg_lst[2] == 'lost':
                await self._conn_lost_f("LOST")
            else:
                await self._conn_lost_f("FOUND")
