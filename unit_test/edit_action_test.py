
import unittest
from unittest import IsolatedAsyncioTestCase
import asyncio
import socket

class MockSocket:
    def __init__(self, port=1339):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to remte server
        self.s.connect(("127.0.0.1" , port))

    def answer(self):
        return self.recvmsg()


# class StackTester(unittest.TestCase):
#     def __init__(self, methodName: str = ...) -> None:
#         super().__init__(methodName)

#     async def call_action(self):
#         await self.server._edit_action("ACT")

#     def xxx(self):
#         self.server = VSCServer(1339)
#         self.reciever = MockSocket(1339)
#         asyncio.run(self.call_action())

#   Server actions: dict   {"Action Name" : Instance}
#   
#
#
#

class EditActionTest(IsolatedAsyncioTestCase):
    
    async def test_empty_string(self):
        self.server = VSCServer(1337)
        self.mockSock = MockSocket(1337)
        await self.server._edit_action("")
        response = self.mockSock.answer()
        print(response)






        
if __name__ == '__main__':
    unittest.main()






# python -m unittest -v test_module //run koden








