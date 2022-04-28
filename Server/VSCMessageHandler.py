import asyncio

ACC_CLIENTS = 1
MSG_LENGTH = 128

END_MSG = "END END_SERVER"
class MsgHandler:
    def __init__(self, port, func):
        self.host = "127.0.0.1"
        self.port = port
        self.running = False
        self.notify_func = func
        self._writer = None
        self._server_task = None
    
    async def start(self):
        if not self.running:
            await asyncio.create_task(self._run_handler()) #asyncio.create_task()

    async def send(self, msg):
        if self.running:
            try:
                self._writer.write(bytes((msg), "utf-8"))
                await self._writer.drain()
            except Exception as e:
                print(e) 

    def exit(self):
        if self.running:
            self.running = False
            self._server_task.cancel()
        
    
    async def _run_handler(self):
        self.running = True
        server = await asyncio.start_server(self._handle_client, self.host, self.port)
        async with server:
            self._server_task = asyncio.create_task(server.serve_forever())
            await self._server_task

    async def _handle_client(self, reader, writer):
        print("Client connected.")
        task_r = asyncio.create_task(self._handle_input(reader))
        self._writer = writer
        try:
            # await self._handle_input(reader)
            await task_r
            self._writer.close()
            await self._writer.wait_closed()
        except asyncio.exceptions.IncompleteReadError as e:
            #print(e)
            self.exit()
        except OSError as e:
            #print(e)
            self.exit()
    
    async def _handle_input(self, reader):
        running_tasks = []
        input_loop = True
        while input_loop:
            msg = await reader.readuntil(b"\t\n")
            print(msg)
            msg = msg.decode("utf-8")[:-2]
            running_tasks.append(asyncio.create_task(self.notify_func(msg)))
            if msg == END_MSG:
                print("Shutting")
                input_loop = False
        await asyncio.gather(*running_tasks)