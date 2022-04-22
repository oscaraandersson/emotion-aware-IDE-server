from inspect import Traceback
from VSCServer import VSCServer
import unittest
import socket
from unittest import IsolatedAsyncioTestCase
import threading
import asyncio

class MockSocket:
    def __init__(self, port) -> None:
        self.port = port
        self.reader = None
        self.writer = None
    async def setup(self):
        self.reader, self.writer = await asyncio.open_connection("127.0.0.1", self.port)

    async def answer(self):
        return (await self.reader.readuntil(bytes("\\","utf-8"))).decode()[:-1]
    
    async def end(self):
        self.writer.write(bytes("END END_SERVER\t\n","utf-8"))
        await self.writer.drain()
        self.writer.close()
        await self.writer.wait_closed()


class EditActionTest(IsolatedAsyncioTestCase):

    async def test_empty_string(self):
        # Asyncio setUp
        self.server = VSCServer(8082)
        self.server_task = asyncio.create_task(self.server.run())
        await asyncio.sleep(0.05)
        self.mockSock = MockSocket(8082)
        await asyncio.sleep(0.05)
        await self.mockSock.setup()
        await asyncio.sleep(0.05)
        
        # Asyncio do
        CONST_STR = "ERR 420 There is no action with the given name. "
        await self.server._edit_action("")
        response = await self.mockSock.answer()
        self.assertEqual(response, CONST_STR)

        # Asyncio teardown
        await self.mockSock.end()
        await self.server_task

if __name__ == "__main__":
    unittest.main()



# cd venv/Scripts
# activate
# cd ../../Server
# python -m unittest -v test_main.py
# cd venv/Scripts && activate && cd ../../Server && python -m unittest -v test_main.py