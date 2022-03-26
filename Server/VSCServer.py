import threading
from Error_handler import ErrorHandler
from VSCMessageHandler import MsgHandler
import asyncio

class E4Server:
    async def scan(self):
        return []
    async def connect(self, address):
        return False
    async def disconnect(self):
        pass

class GazePoint:
    def start():
        pass
    def recalibrate():
        pass
    def stop():
        pass

CMD_EYE = "EYE"
CMD_AVAILABLE_E4 = "AVE4"


class VSCServer:
    def __init__(self, port=1337):
        self.errh = ErrorHandler()
        self.server_E4 = E4Server()
        self.eye_tracker = GazePoint()
        self.msg_handler = MsgHandler(port, self._handle_incomming_msg)
        self.msg_thread = threading.Thread(target=self.msg_handler.start)
        self.msg_thread.start()
        self.cmd_dict = {
            "FRM" : self._save_form_data,
            "CE4" : self._connect_E4,
            "DE4" : self._disconnect_E4,
            "ONEY": self._start_eyetracker,
            "OFEY": self._stop_eyetracker,
            "RCEY": self._recalibrate_eyetracker,
            "END" : self._end_server,
            "SBL" : self._start_baseline,
            "SCE4": self._scan_E4
        }

    def __del__(self):
        self.msg_thread.join()

    def _handle_incomming_msg(self, msg):
        # Message format CMD {Data}
        seperator = msg.find(" ")
        cmd = msg[:seperator]
        data = msg[seperator+1:]
        if cmd in self.cmd_dict:
            self.cmd_dict[cmd](data)
        else:
            self._send_error(self.errh.ERR_INVALID_CMD)
    
    async def _send_error(self, err):
        self.msg_handler.send(self.errh[err])

    async def _save_form_data(self, data):
        # Handle form (for training AI)
        print(data)
    
    async def _start_baseline(self, data):
        # Record
        pass

    async def _end_server(self, data):
        pass 
    
    async def _connect_E4(self, data):
        connected = await E4Server.connect(data)
        if not connected:
            self._send_error(self.errh.ERR_E4_NOTFOUND)   

    async def _disconnect_E4(self, data):
        self.server_E4.disconnect()

    async def _start_eyetracker(self, data):
        self.eye_tracker.start()
        msg = CMD_EYE
        msg += " SUCCESS"
        self.msg_handler.send(msg)

    async def _stop_eyetracker(self, data):
        self.eye_tracker.stop()
        msg = CMD_EYE
        msg += " SUCCESS"
        self.msg_handler.send(msg)

    async def _recalibrate_eyetracker(self, data):
        self.eye_tracker.recalibrate()
        msg = CMD_EYE
        msg += " SUCCESS"
        self.msg_handler.send(msg)

    async def _scan_E4(self, data):
        address_lst = self.server_E4.scan()
        if address_lst:
            msg = CMD_AVAILABLE_E4
            for address in address_lst:
                msg += " " + address
            self.msg_handler.send(msg)
        else:
            self._send_error(self.errh.ERR_E4_NOTFOUND)

if __name__ == "__main__":
    server = VSCServer()