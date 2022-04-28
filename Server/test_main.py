# Please excuse us not using setUp/tearDown for some reason it didn't want to work with async
from http.client import EXPECTATION_FAILED
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
        return (await self.reader.readuntil(bytes("\t\n","utf-8"))).decode()[:-2]
    
    async def end(self):
        self.writer.write(bytes("END END_SERVER\t\n","utf-8"))
        await self.writer.drain()
        self.writer.close()
        await self.writer.wait_closed()

async def asyncio_setUp(self):
    # Asyncio setup (Error when using setUp in class)
    self.server = VSCServer(1340)
    self.server_task = asyncio.create_task(self.server.run())
    await asyncio.sleep(0.05)
    self.mockSock = MockSocket(1340)
    await asyncio.sleep(0.05)
    await self.mockSock.setup()
    await asyncio.sleep(0.05)

async def asyncio_tearDown(self):
    await self.mockSock.end()
    await self.server_task

def get_action_values(self, act):
    return {
        "active" : self.server.actions[act].active,
        "running" : self.server.actions[act].running
    }

class EditActionTest(IsolatedAsyncioTestCase):

    async def test_statement_Figure2_1(self):
        await asyncio_setUp(self)
        # Asyncio do
        EXPECTED_RESPONSE = "ERR 420 There is no action with the given name. "
        await self.server._edit_action("")
        response = await self.mockSock.answer()
        
        await asyncio_tearDown(self)
        
        self.assertEqual(response, EXPECTED_RESPONSE)
    
    async def test_statement_Figure2_2(self):
        # Asyncio setUp
        await asyncio_setUp(self)

        # Asyncio do
        EXPECTED_RESPONSE = "EACT SUCC"
        await self.server._edit_action("TEST TIME 0.001")
        response = await self.mockSock.answer()
        
        await asyncio_tearDown(self)
        
        self.assertEqual(response, EXPECTED_RESPONSE)


    async def test_statement_Figure2_3(self):
        # Asyncio setup
        await asyncio_setUp(self)

        EXPECTED_RESPONSE = "ERR 425 Settings are not available for action. NOSETTING"
        await self.server._edit_action("TEST NOSETTING :(")
        response = await self.mockSock.answer()
        
        await asyncio_tearDown(self)
        
        self.assertEqual(response, EXPECTED_RESPONSE)



    # # decision coverage path no. 1 is already covered in statement test case
    
    async def test_decision_Figure2_1(self):
        await asyncio_setUp(self)

        EXPECTED_RESPONSE = "ERR 425 Settings are not available for action. NOSETTING ESTM 1"
        await self.server._edit_action("TEST NOSETTING :( ESTM TIME 1")
        response = await self.mockSock.answer()
        
        await asyncio_tearDown(self)
        
        self.assertEqual(response, EXPECTED_RESPONSE)
        
    
    async def test_decision_Figure2_2(self):
        await asyncio_setUp(self)
        
        EXPECTED_RESPONSE = "EACT SUCC"
        await self.server._edit_action("TEST")
        response = await self.mockSock.answer()
        
        await asyncio_tearDown(self)
        
        self.assertEqual(response, EXPECTED_RESPONSE)

        
        
    # Path coverage covered by earlier test cases
        
        
        
###figure1
        
        
        
    async def test_statement_Figure1_1(self):
        await asyncio_setUp(self)
        await self.server._activate_action("TEST")
        EXPECTED_VALUES = get_action_values(self, "TEST")

        await self.server._deactivate_action("TEST")
        response = get_action_values(self, "TEST")
        
        await asyncio_tearDown(self)
        
        self.assertDictEqual(EXPECTED_VALUES, response)




    async def test_decision_Figure1_2(self):
        await asyncio_setUp(self)
        
        EXPECTED_VALUES = get_action_values(self, "TEST")
        await self.server._deactivate_action("TEST")
        response = get_action_values(self, "TEST")
        
        await asyncio_tearDown(self)
        
        self.assertDictEqual(EXPECTED_VALUES, response)
        
        
    async def test_decision_Figure1_3(self):
        
        await asyncio_setUp(self)
        
        EXPECTED_VALUES = "DACT SUCC "
        await self.server._deactivate_action("")
        response = await self.mockSock.answer()

        await asyncio_tearDown(self)
        
        self.assertEqual(EXPECTED_VALUES, response)
            
        
    # Path coverage is already covered in above test cases
        

# #figure 3

    async def test_statement_Figure3_1(self):
        await asyncio_setUp(self)
        
        EXPECTED_RESPONSE = "AACT FAIL TEST2"
        await self.server._activate_action("TEST2")
        response = await self.mockSock.answer()
        
        await asyncio_tearDown(self)
        
        self.assertEqual(EXPECTED_RESPONSE, response)
        
    

        
    async def test_statement_Figure3_2(self):
        await asyncio_setUp(self)
        
        EXPECTED_RESPONSE = "AACT SUCC"
        await self.server._activate_action("")
        response = await self.mockSock.answer()
        
        await asyncio_tearDown(self)
        
        self.assertEqual(EXPECTED_RESPONSE, response)
        



    async def test_decision_Figure3_2(self):
        await asyncio_setUp(self)
        self.server.actions["TEST"].running = True
        
        EXPECTED_RESPONSE = "AACT SUCC"
        await self.server._activate_action("TEST")
        response = await self.mockSock.answer()

        await asyncio_tearDown(self)
        
        self.assertEqual(EXPECTED_RESPONSE, response)


    async def test_decision_Figure3_3(self):
        await asyncio_setUp(self)

        EXPECTED_RESPONSE = "AACT SUCC"
        await self.server._activate_action("TEST")
        response = await self.mockSock.answer()
        
        await asyncio_tearDown(self)

        self.assertEqual(EXPECTED_RESPONSE, response)
        
    async def test_decision_Figure3_4(self):
        await asyncio_setUp(self)
        EXPECTED_RESPONSE = "AACT SUCC"

        await self.server._activate_action("NOACTION")
        response = await self.mockSock.answer()
        
        await asyncio_tearDown(self)

        self.assertEqual(EXPECTED_RESPONSE, response)
        
        
        
    async def test_path_Figure3_2(self):
        await asyncio_setUp(self)
        EXPECTED_VALUES = {
            "TEST2" : {"active" : True, "running" : True},
            "TEST" : {"active" : True, "running" : True}
            }
        self.server.settings["devices"]["TEST"] = True

        await self.server._activate_action("TEST2")
        await asyncio.sleep(0.1)
        values = {
            "TEST2" : get_action_values(self, "TEST2"),
            "TEST" : get_action_values(self, "TEST")
        }
        
        await asyncio_tearDown(self)

        self.assertEqual(EXPECTED_VALUES, values)


        
    async def test_path_Figure3_3(self):
        await asyncio_setUp(self)
        EXPECTED_RESPONSE = "AACT FAIL TEST4"
        self.server.settings["devices"]["TEST"] = True
        
        await self.server._activate_action("TEST2 TEST4")
        response = await self.mockSock.answer()
        
        await asyncio_tearDown(self)

        self.assertEqual(EXPECTED_RESPONSE, response)


        
    async def test_path_Figure3_5(self):
        await asyncio_setUp(self)
        EXPECTED_RESPONSE = "AACT FAIL TEST2"

        await self.server._activate_action("TEST2")
        response = await self.mockSock.answer()

        await asyncio_tearDown(self)

        self.assertEqual(EXPECTED_RESPONSE, response)


if __name__ == "__main__":
    unittest.main()



# cd venv/Scripts
# activate
# cd ../../Server
# python -m unittest -v test_main.py
# D: && cd Users/Benis.Barker/EmoIDE/Server-side/venv/Scripts && activate && cd ../../Server && python -m unittest -v test_main.py