from Error_handler import ErrorHandler
from VSCMessageHandler import MsgHandler
from VSCServerMessages import *
from e4Handler import E4
from ActionFactory import action_factory
import asyncio
import sys
import json
import numpy as np

sys.path.append("../machine_learning")
sys.path.append("../")

import machine_learning




class GazePoint:
    def start():
        pass
    def recalibrate():
        pass
    def stop():
        pass

BASELINE_TIME = 30 # Last 30 seconds
BASELINE_NAME = "lokal_baseline.json"

def blahblah():
    with open("Baselineout.json","r") as opfile:
        dic = {}
        for key, val in json.load(opfile).items():
            dic[key] = np.array(val)
        return machine_learning.E4model(dic)

class VSCServer:
    def __init__(self, port=1339):
        self.errh = ErrorHandler()
        self._E4_handler = E4(self._connected_confirmation, self._lost_E4_connection)
        self._E4_model = blahblah()
        self.eye_tracker = GazePoint()
        self._baseline = None
        self.settings = {
            "devices" : {"E4" : True, "EYE" : False, "EEG" : False},
            "setup" : True
        }
        self.actions = action_factory(self)
        self.act_waiting = {}
        self.msg_handler = MsgHandler(port, self._handle_incomming_msg)
        self.handler_task = asyncio.create_task(self.msg_handler.start())
        self.done_lock = asyncio.Event()
        self.cmd_dict = {
            "FRM" : self._save_form_data,         # Form, training AI
            "CE4" : self._connect_E4,             # Connect E4
            "DE4" : self._disconnect_E4,          # Disconnect E4
            "ONEY": self._start_eyetracker,       # Start EYE
            "OFEY": self._stop_eyetracker,        # Stop EYE
            "RCEY": self._recalibrate_eyetracker, # Recalibrate EYE
            "END" : self._end_server,             # End server (exit)
            "SBL" : self._start_baseline,         # Start basline recording
            "SCE4": self._scan_E4,                # Scan for E4 devices
            "AACT": self._activate_action,
            "DACT": self._deactivate_action,
            "EACT": self._edit_action,
            "ACT": self._action_response
        }
    
    async def run(self):
        try:
            await self.handler_task
        except asyncio.CancelledError:
            print("Server shut down successfull.")

    async def _activation_check(self, act):
        def actions_traverse(visited, current):
            visited.add(current)
            if not self.actions[current]["act"]:
                return visited
            for a in self.actions[current]["act"]:
                if not a in visited:
                    visited.update(actions_traverse(visited, a))
            return visited

        for d in self.actions[act]["devices"]:
            if not self.settings["devices"][d]:
                return []
        
        return list(actions_traverse(set(), act))

    async def _activate_action(self, msg):
        # Desired actions splitted with a space
        action_lst = msg.split(' ')
        # action which device(s) are not connected
        cannot_activate = []
        for a in action_lst:
            if a in self.actions:
                depend_act = await self._activation_check(a)
                print("Activating: " + str(depend_act))
                # Check that all required devices are connected
                for d in depend_act:
                    if not self.actions[d]["running"]:
                        self.actions[d]["active"] = True
                        self.actions[d]["running"] = True
                        asyncio.create_task(self.actions[d]["obj"].start())
                if not depend_act and self.actions[a]["client"]:
                    cannot_activate.append(a)
        if cannot_activate:
            # Return all actions which could not be connected
            await self.send(ACTIVATE_ACTION+" ERR "+" ".join(cannot_activate))
        else:
            # All actions are active 
            await self.send(ACTIVATE_ACTION +" "+SUCCESS_STR)

    async def _deactivate_action(self, msg):
        action_lst = msg.split(' ')
        client_actions = []
        # Deactivate all actions
        for act in action_lst:
            shut_down = await self.actions[act]['obj'].exit()
            print("Shutting down: " + str(shut_down))
            for a in shut_down:
                self.actions[a]["active"] = False
                self.actions[a]["running"] = False
                if self.actions[a]["client"]:
                    client_actions.append(a)
                if a in self.act_waiting:
                    del self.act_waiting[a]
        await self.send(DEACTIVATE_ACTION +" "+ SUCCESS_STR+" "+" ".join(client_actions))
    
    async def _edit_action(self, data):
        cmd_parts = data.split(" ")
        a = cmd_parts[0]
        if not a in self.actions:
            self._send_error(self.errh.ERR_NOT_AN_ACTION, a)
            return
        cmd_parts = cmd_parts[1:]
        not_changed = []
        not_a_setting = []
        for i in range(0,len(cmd_parts), 2):
            s = cmd_parts[i]
            if s in self.actions[a]["obj"].settings:
                changed = self.actions[a]["obj"].settings[s](cmd_parts[i+1])
                if not changed:
                    not_changed.append(s)
            else:
                not_a_setting.append(s)
        response = ""
        if not_a_setting:
            response = " ".join(not_a_setting)
            await self._send_error(self.errh.ERR_NOT_A_SETTING,response)
        if not_changed:
            await self.send(EDIT_ACTION+" "+FAIL_STR+" "+" ".join(not_changed))
        if not (not_a_setting and not_changed):
            await self.send(EDIT_ACTION+" "+SUCCESS_STR)

        


    async def _handle_incomming_msg(self, msg):
        # Message format CMD {Data}
        data = ""
        seperator = msg.find(" ")
        # Command to call
        if seperator == -1:
            cmd = msg
        else:
            cmd = msg[:seperator]
        # Data sent to the function mapped to the command
        data = msg[seperator+1:]
        if cmd in self.cmd_dict:
            # Call function with data
            await self.cmd_dict[cmd](data)
        else:
            # Throw error, non existant command
            await self._send_error(self.errh.ERR_INVALID_CMD)
    
    async def _send_error(self, err, msg=""):
        # Send error to client
        await self.msg_handler.send(self.errh[err]+" "+msg)
    
    async def action_send(self, act, data):
        # Send data to extension from action, one way communication
        msg = ACTION_STR +" "+ act +" "+ data
        await self.send(msg)

    async def action_send_wait(self, act, data):
        # Send data to extension and wait for response
        msg = ACTION_STR +" "+ act +" "+ data
        # Put the action in waiting list
        self.act_waiting[act] = self.actions[act]["obj"]
        # Send message to client
        await self.send(msg)

    async def _action_response(self, msg):
        seperator = msg.find(" ")
        # Action name is first argument is msg
        name = msg[:seperator]
        data = msg[seperator+1:]
        if name in self.act_waiting:
            # Send response to client
            self.act_waiting[name].client_response(data)
            # Remove action from waiting list
            del self.act_waiting[name]

    
    async def send(self, msg):
        await self.msg_handler.send(msg)

    async def _save_form_data(self, data):
        # Handle form (for training AI)
        print(data)
    
    async def _save_baseline(self, baseline):
        with open("lokal_baseline.json","w") as opfile:
            json.dump(baseline, opfile, indent=4)

    def _to_baseline(self, stream_data):
        ret_dict = {}
        for key, val in stream_data.items():
            val1 = []
            if key != "timestamp":
                val1 = np.array(val)
            else:
                val1 = val
            ret_dict[key] = val1
        return ret_dict

    async def _read_baseline(self):
        with open("VSCBaseline.json","r") as opfile:
            baseline = json.load(opfile)
        return self._to_baseline(baseline)


    async def _start_baseline(self, data):
        # Record baseline, subscribe to feed
        # Make sure E4 is connected
        cmd_lst = data.split(" ")
        if cmd_lst[0] == "OLD":
            # Try to load to already recorded baseline
            response = " Baseline loaded, start developing!"
            if self._baseline == None:
                response = " No earlier recorded baseline."
                # Let extension know a new baseline must be loaded
                await self.send(START_BASELINE+" "+FAIL_STR+response)
                return None
            baseline = await self._read_baseline()
            # Create E4 prediction model
            self._E4_model = machine_learning.E4model(baseline)
            # Let extension know baseline is loaded
            await self.send(START_BASELINE+" "+SUCCESS_STR+response)
        else:
            response = " Baseline set, start developing!"
            # Check if E4 is connected
            if self.settings["devices"]["E4"]:
                # Wait for the whole baseline to be recorded
                await asyncio.sleep(BASELINE_TIME+3)
                # Get data to be converted to baseline
                stream_data = self._E4_handler.get_data(BASELINE_TIME)
                # Create baseline
                self._baseline = self._to_baseline(stream_data)
                # Save baseline lokaly, loading baseline is now possible
                await self._save_baseline(stream_data)
                # Create E4 prediction model
                self._E4_model = machine_learning.E4model(self._baseline)
                # Let extension know the new baseline is set
                await self.send(START_BASELINE +" "+ SUCCESS_STR+response)
            else:
                # Let extension know that connection to E4 is required to create
                # a new baseline
                response = " E4 not connected, connect the device and try again!"
                await self.send(START_BASELINE +" "+ FAIL_STR+response)

    async def _end_server(self, data):
        await self._save_actions()
        self.handler_task.cancel()
    
    async def _save_actions(self):
        pass

    async def _get_saved_actions(self):
        return ["TEST"] 
    
    async def _activate_active_actions(self):
        for a in self.actions.keys():
            all_devices_connected = True
            for d in self.actions[a]["devices"]:
                if not self.settings["devices"][d]:
                    all_devices_connected = False
            if self.actions[a]["active"] and all_devices_connected:
                await self.actions[a]["obj"].start()

    async def _connect_E4(self, data):
        await self._E4_handler.connect(data)

    async def _disconnect_E4(self, data):
        self._E4_handler.disconnect()


    async def _start_eyetracker(self, data):
        self.eye_tracker.start()
        await self.send(START_EYE +" "+ SUCCESS_STR)

    async def _stop_eyetracker(self, data):
        self.eye_tracker.stop()
        await self.send(STOP_EYE +" "+ SUCCESS_STR)

    async def _recalibrate_eyetracker(self, data):
        self.eye_tracker.recalibrate()
        await self.send(RECALIBRATE_EYE +" "+ SUCCESS_STR)

    async def _scan_E4(self, data):
        address_lst = await self._E4_handler.scan_for_e4()
        if address_lst:
            msg = SCAN_E4 +" "+ SUCCESS_STR
            for address in address_lst:
                msg += " " + address
            await self.send(msg)
        else:
            await self.send(SCAN_E4 +" "+ FAIL_STR)
    
    async def _lost_E4_connection(self):
        for f in self.actions:
            if "E4" in self.actions[f]["devices"]:
                try:
                    await self.actions[f]["obj"].exit()
                except asyncio.CancelledError:
                    print(f"Action '{f}' was cancelled due to connection lost to E4")
                self.actions[f]["running"] = False
                if f in self.act_waiting:
                    del self.act_waiting[f]
        await self.send(E4_LOST_CONNECTION + " Lost connection to device.")

    async def _connected_confirmation(self):
        self.settings["devices"]["E4"] = True
        await self._activate_active_actions()
        await self.send(f"{CONNECT_E4} {SUCCESS_STR}")

async def main():
    server = VSCServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
