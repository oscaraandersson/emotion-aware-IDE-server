import asyncio

ACC_CLIENTS = 1
MSG_LENGTH = 128
QUIT_MESSAGE = "END_STREAM"

class MsgHandler:
    def __init__(self, port, func):
        self.host = "127.0.0.1"
        self.port = port
        self.running = False
        self.notify_func = func
        self._message = ""
        self._exists_message = None
        self._event_loop = None
    
    def start(self):
        asyncio.run(self._run_handler())
    
    def send(self, msg):
        print(self.running)
        if self.running:
            self._message = bytes(msg, "utf-8")
            self._event_loop.call_soon_threadsafe(self._exists_message.set)
    
    def _exit(self):
        self.running = False
        self._exists_message.set()
        
    
    async def _run_handler(self):
        self.running = True
        self._exists_message = asyncio.Event()
        self._event_loop = asyncio.get_event_loop()
        server = await asyncio.start_server(self._handle_client, self.host, self.port)
        async with server:
            await server.serve_forever()
    
    async def _handle_client(self, reader, writer):
        tasks = []
        tasks.append(self._handle_input(reader))
        tasks.append(self._handle_output(writer))
        await asyncio.gather(*tasks)

    
    async def _handle_input(self, reader):
        while self.running:
            msg = await reader.readuntil(b"\t\n")
            msg = msg.decode("utf-8")[:-2]
            self.notify_func(msg)

    async def _handle_output(self, writer):
        while self.running:
            await self._exists_message.wait()
            if self._message:
                writer.write(self._message)
                await writer.drain()
                self._message = b""
            self._exists_message.clear()

