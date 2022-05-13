import asyncio
import enum
from sre_constants import CALL
from e4Client import E4Handler
from enum import Enum
import inspect
import time

class E4data(Enum):
    BVP = "bvp"
    ACC = "acc"
    GSR = "gsr"
    IBI = "ibi"
    TEMP = "tmp"
    BAT = "bat"
    TAG = "tag"
    HR = "hr"

CORRECT_DATA = ["bvp","acc","gsr","ibi","tmp","bat","tag"]

STREAM_FROM = {
    E4data.BVP : "E4_Bvp",
    E4data.ACC : "E4_Acc",
    E4data.GSR : "E4_Gsr",
    E4data.TEMP: "E4_Temp",
    E4data.IBI : "E4_ibi",
    E4data.HR  : "E4_Hr",
    E4data.BAT : "E4_Battery",
    E4data.TAG : "E4_Tag"
}

def handle_e4_list(l_str):
    e4_list = []
    temp_lst = l_str.split(' | ')
    cmd_lst = temp_lst[0].split(' ')
    no_items = int(cmd_lst[2])
    if no_items > 0:
        devices = temp_lst[1:]
        for i in range(no_items):
            e4_list.append(devices[i].split(' ')[0])
    return e4_list

def handle_e4_subscription(s_str):
    if s_str.split(' ')[3] == "OK":
        return True
    return False

SECONDS_TO_SAVE = 30

class E4:
    def __init__(self):
        self._E4_client = E4Handler(self._dc_callback)
        self._connected = False
        self.dc_func = None
        self.dataObject = {
                "EDA": [],
                "BVP": [],
                "TEMP": [],
                "HR" : [],
                "timestamp": 0
                }
        self._add_callbacks()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, type, value, traceback):
        await self._E4_client.exit()

    async def exit(self):
        await self._E4_client.exit()

    def _add_callbacks(self):
        self._E4_client.callback('E4_Acc' ,self._ACC)
        self._E4_client.callback('E4_Bvp' ,self._BVP)
        self._E4_client.callback('E4_Gsr' ,self._GSR)
        self._E4_client.callback('E4_Temperature',self._TEMP)
        self._E4_client.callback('E4_Ibi' ,self._IBI)
        self._E4_client.callback('E4_Hr' ,self._HR)
        self._E4_client.callback('E4_Battery',self._BATTERY)
        self._E4_client.callback('E4_Tag', self._TAG)

    def _BVP(self, timestamp, data):
        self.dataObject["BVP"].append(data[0])
        if len(self.dataObject["BVP"]) % ((SECONDS_TO_SAVE*64)+1) == 0:
            self.dataObject["BVP"].pop(0)
        
    def _ACC(self, timestamp, data):
        pass

    def _GSR(self, timestamp, data):
        self.dataObject["EDA"].append(data[0])
        if len(self.dataObject["EDA"]) % ((SECONDS_TO_SAVE*4)+1) == 0:
            self.dataObject["EDA"].pop(0)

    def _TEMP(self, timestamp, data):
        self.dataObject["TEMP"].append(data[0])
        if len(self.dataObject["TEMP"]) % ((SECONDS_TO_SAVE*4)+1) == 0:
            self.dataObject["TEMP"].pop(0)

    def _IBI(self, timestamp, data):
        pass

    def _HR(self, timestamp, data):
        self.dataObject["HR"].append(data[0])
        if len(self.dataObject["HR"]) % (SECONDS_TO_SAVE+1) == 0:
            self.dataObject["HR"].pop(0)

    def _BATTERY(self, timestamp, data):
        pass
    def _TAG(self, timestamp, data):
        pass

    async def _dc_callback(self, state):
        if self.dc_func is not None:
            if inspect.iscoroutinefunction(self.dc_func):
                await self.dc_func(state)
            else:
                self.dc_func(state)
    
    def disconnect_callback(self, func):
        self.dc_func = func

    async def connect_to_server(self, port=28000):
        if not self._connected:
            wait_event = asyncio.Event()
            await self._E4_client.start(port, wait_event)
            await wait_event.wait()
            self._connected = self._E4_client.ensure_connection()
        return self._connected

    async def connect_E4_device(self, d_name = "082FCD"):
        if not self._connected:
            raise Exception("Server is not connected.")
        response = await self._E4_client.send("device_connect", d_name)
        parts = response.split(' ')
        if parts[2] == "OK":
            return True
        return False
    
    async def connect_E4(self):
        if not self._connected:
            raise Exception("Server is not connected.")
        device_lst = handle_e4_list(await self._E4_client.send("device_list"))
        if device_lst:
            return await self.connect_E4_device(device_lst[0])
        return False
    
    async def disconnect_E4(self):
        """
            Returns True if device was disconnected,
            Returns False if there was no device to disconnect
            After calling this function a new connection to the
            E4 Streaming Server needs to be established
        """
        if not self._connected:
            raise Exception("Server is not connected.")
        response = await self._E4_client.send("device_disconnect")
        parts = response.split(' ')
        self._connected = False
        await self._E4_client.exit()
        if parts[2] == "OK":
            # Disconnected device
            return True
        # No device connected in the first place
        return False
    
    async def subscribe_to(self, enum_sub):
        if not self._connected:
            raise Exception("Server is not connected.")
        sub = enum_sub.value
        success = False
        if sub in CORRECT_DATA:
            resp = await self._E4_client.send("device_subscribe", f"{sub} ON")
            if resp.split(' ')[3] == "OK":
                success = True
        return success

    async def pause_E4(self, status=True):
        """
         Returns True if the connected device was false
         Returns False if there was no connected device to pause
        """
        if not self._connected:
            raise Exception("Server is not connected.")
        msg = "OFF"
        if status:
            msg = "ON"
        response = await self._E4_client.send("pause",msg)
        if response.split(' ')[2] == "OK":
            return True
        return False
    
    def get_data(self, no_seconds):
        if no_seconds > SECONDS_TO_SAVE:
            raise Exception(f"To many seconds. Only the last {SECONDS_TO_SAVE} seconds are stored.")
        if no_seconds > len(self.dataObject["HR"]):
            raise Exception("There is not enough data.")
        data_object = {}
        data_object["EDA"] = self.dataObject["EDA"][-4*no_seconds:]
        data_object["BVP"] = self.dataObject["BVP"][-64*no_seconds:]
        data_object["TEMP"] = self.dataObject["TEMP"][-4*no_seconds:]
        data_object["HR"] = self.dataObject["HR"][-1*no_seconds:]
        data_object["timestamp"] = time.time()
        return data_object



async def main():
    e4 = E4()
    e4.disconnect_callback(lambda state : print(state))
    connected = await e4.connect_to_server()
    if connected:
        await e4.connect_E4()
        await e4.subscribe_to(E4data.IBI)
        await asyncio.sleep(10)
        await e4.disconnect_E4()
    await e4.exit()

if __name__ == "__main__":
   asyncio.run(main())