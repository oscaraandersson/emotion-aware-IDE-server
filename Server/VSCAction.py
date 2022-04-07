import asyncio
import json
import numpy as np
import pandas as pd
from VSCServerMessages import *
import time
import os

class Action:
    def __init__(self, frequency, serv):
        # Needs to be set when creating a new action
        
        self.NAME = "ACT1"
        self.CLIENT_ACTION = True
        self.DEVICES = []
        # If an action is dependent on another action
        # !OBS! If dependent on another action, its device
        # dependencies are transferred over to this actions DEVICES
        self.ACTIONS = []
        # --------------------------------------------
        # Do not worry about these
        
        self.serv = serv
        self.main_task = None
        self._subscriptions = []
        self.client_answer_lock = asyncio.Event()
        self._client_answer_message = ""
        # --------------------------------------------
        # Available for changes during runtime in _execute()

        self.running = False
        self.time = 1/frequency
        self.settings = {
            "TIME" : self._set_time
        }
    # ------------------------------------------------
    # -------------- Core functions ------------------
    # ------------------------------------------------
    async def start(self):
        # Starts the scheduler, waits for main_task to be done
        self.running = True
        self.main_task = asyncio.create_task(self._scheduler())
        await self.main_task
    
    async def exit(self):
        # Resets variables if action is to be activated again
        shut_down = []
        if self.running:
            self.running = False
            self._client_answer_message = ""
            self.client_answer_lock.clear()
            shut_down = await self._shutdown_dependent()
            if self.main_task != None:
                # Abruptly cancel, cancels all waiting
                # coroutines
                self.main_task.cancel()
                try:
                    await self.main_task
                except asyncio.CancelledError:
                    pass
        return shut_down

    async def _scheduler(self):
        while self.running:
            # Sleeps inbetween work
            await asyncio.sleep(self.time)
            if self.running:
                # Do work
                await self._execute()
    # -------------------------------------
    # -------- Messaging client -----------
    # -------------------------------------
    def client_response(self, data):
        if self.running:
            # Save response to class variable
            self._client_answer_message = data
            # Let action know message have been recieved
            self.client_answer_lock.set()        
    
    async def _msg_client(self, data):
        # Send message to client, no response expected
        await self.serv.action_send(self.NAME, data)

    async def _msg_client_wait(self, data):
        # Send message to client
        await self.serv.action_send_wait(self.NAME, data)
        # Wait for response
        await self.client_answer_lock.wait()
        # Response recieved, reset lock for use next time
        self.client_answer_lock.clear()
        # Return recieved message
        return self._client_answer_message

    # ---------------------------------------------
    # ------------- Safe deactivation -------------
    # ---------------------------------------------
    def observe(self, act):
        self._subscriptions.append(act)
    
    async def _shutdown_dependent(self):
        shut_down = []
        for a in self._subscriptions:
            shut_down.extend(await a.exit())
        shut_down.append(self.NAME)
        return shut_down

    # ---------------------------------------------
    # ---------------- Execution ------------------
    # ---------------------------------------------
    
    def _set_time(self, new_time):
        changed = True
        try:
            self.time = float(new_time)
        except Exception:
            changed = False
        return changed

    async def _execute(self):
        pass

class SurveyAction(Action):
    def __init__(self, frequency, serv):
        super().__init__(frequency, serv)
        # - - NECESSARY - -
        self.NAME = "SRVY"
        self.DEVICES = ["E4"]
        # -----------------

        self.DATA_RANGE = 10
    
    async def _execute(self):
        # Request mood from extension, wait for response
        FILE_NAME = "training_data.json"
        message = await self._msg_client_wait("MOOD")
        # Get data to pair mood with
        latest_data = await self.serv.server_E4.get_data(self.DATA_RANGE)
        # Add mood to data
        latest_data["value"] = int(message)
        # Write to disk for later training of AI
        if not os.path.exists(FILE_NAME):
            temp_file = open(FILE_NAME, "w")
            temp_file.close()
        
        with open(FILE_NAME,"r+") as opfile:
            try:
                existing_data = json.load(opfile)
            except json.decoder.JSONDecodeError:
                existing_data = []
            opfile.seek(0,0)
            existing_data.append(latest_data)
            json.dump(existing_data, opfile, indent=4)

class EstimatedEmotion(Action):
    def __init__(self, frequency, serv):
        super().__init__(frequency, serv)
        self.NAME = "ESTM"
        self.DEVICES = ["E4"]
        self._signal_index = 0
    
    def _convert(self, latest_data):
        ret_dict = {}
        for key, val in latest_data.items():
            ret_dict[key] = np.array(val)
        return ret_dict
    
    def _save_prediction(self, index):
        # Check if csv file already exists
        FILE_NAME = "../../Dashboard/emotions.csv"
        df = None

        if os.path.exists(FILE_NAME):
            df = pd.read_csv(FILE_NAME)
        else:
            df = pd.DataFrame({
                "timestamp" : [],
                "emotions" : []
            })
        timestamp = int(time.time())
        df1 = pd.DataFrame({
            "timestamp" : [timestamp],
            "emotions" : [index]
        })
        df = pd.concat([df, df1], ignore_index=True)
        df.to_csv(FILE_NAME, index=False)

    async def _execute(self):
        latest_data = await self.serv._E4_handler.get_data(self.DATA_RANGE)
        # Temporary until we get actual streaming from E4
        with open("SignalOut.json", "r") as opfile:
            latest_data = json.load(opfile)

        # Convert to correct format before using with E4Model
        signal_values = self._convert(latest_data[self._signal_index])
        # Temporary until we get actual streaming from E4
        self._signal_index = (self._signal_index + 1) % 6
        # Make prediction
        pred_lst = self.serv._E4_model.predict(signal_values)
        # Get the prediction with highest certainty
        max_pred = max(pred_lst)
        # Get index of said prediction
        pred_index = pred_lst.index(max_pred) + 1
        # Save prediction to disk, for use in Dashboard
        self._save_prediction(pred_index)
        # Send prediction to client
        msg = f"{str(pred_index)} {str(round(max_pred*100, 1))}"
        await self._msg_client(msg)

class TestAction(Action):
    def __init__(self, frequency, serv):
        super().__init__(frequency, serv)
        self.NAME = "TEST"
    
    async def _execute(self):
        print("Sending")
        print(await self._msg_client_wait("Tjabba"))
