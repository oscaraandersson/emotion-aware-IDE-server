import asyncio
import json
import numpy as np
import pandas as pd
from VSCServerMessages import *
import time
import os

feature_order = {
        'mean_SCL': [],
        'AUC_Phasic' : [],
        'min_peak_amplitude' : [],
        'max_peak_amplitude' : [],
        'mean_phasic_peak' : [],
        'sum_phasic_peak_amplitude' : [],
        'mean_temp' : [],
        'mean_temp_difference' : [],
        'max_temp' : [],
        'max_temp_difference' : [],
        'min_temp' : [],
        'min_temp_difference' : [],
        'difference_BVPpeaks_ampl' : [],
        'mean_BVPpeaks_ampl' : [],
        'min_BVPpeaks_ampl' : [],
        'max_BVPpeaks_ampl' : [],
        'sum_peak_ampl' : [],
        'HR_mean_difference' : [],
        'HR_variance_difference' : [],
        'label' : []
}

class Action:
    def __init__(self, frequency, serv):
        # Needs to be set when creating a new action
        
        self.NAME = "ACT1"
        self.CLIENT_ACTION = True
        self.DEVICES = []
        self.ACTIONS = []
        self.active = False
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
        if not self.running:
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
            # Response from client saved in class variable
            self._client_answer_message = data
            self.client_answer_lock.set()        
    
    async def _msg_client(self, data):
        # Send message to client, no response expected
        await self.serv.action_send(self.NAME, data)

    async def _msg_client_wait(self, data):
        # Send message to client and wait for response
        await self.serv.action_send_wait(self.NAME, data)
        
        await self.client_answer_lock.wait()
        self.client_answer_lock.clear()

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

    def _convert(self, latest_data):
        ret_dict = {}
        for key, val in latest_data.items():
            ret_dict[key] = np.array(val)
        return ret_dict

    def _save_instance(self, instance, label):
        # Check if csv file already exists
        FILE_NAME = "dataset.csv"
        df = None

        if os.path.exists(FILE_NAME):
            df = pd.read_csv(FILE_NAME)
        else:
            df = pd.DataFrame(feature_order)
        df1 = pd.DataFrame({
            'mean_SCL': [instance[0]],
            'AUC_Phasic' : [instance[1]],
            'min_peak_amplitude' : [instance[2]],
            'max_peak_amplitude' : [instance[3]],
            'mean_phasic_peak' : [instance[4]],
            'sum_phasic_peak_amplitude' : [instance[5]],
            'mean_temp' : [instance[6]],
            'mean_temp_difference' : [instance[7]],
            'max_temp' : [instance[8]],
            'max_temp_difference' : [instance[9]],
            'min_temp' : [instance[10]],
            'min_temp_difference' : [instance[11]],
            'difference_BVPpeaks_ampl' : [instance[12]],
            'mean_BVPpeaks_ampl' : [instance[13]],
            'min_BVPpeaks_ampl' : [instance[14]],
            'max_BVPpeaks_ampl' : [instance[15]],
            'sum_peak_ampl' : [instance[16]],
            'HR_mean_difference' : [instance[17]],
            'HR_variance_difference' : [instance[18]],
            'label' : [label]
        })
        df = pd.concat([df, df1], ignore_index=True)
        df.to_csv(FILE_NAME, index=False)

    async def _execute(self):
        # Request mood from extension, wait for response
        message = await self._msg_client_wait("MOOD")

        if message != "0":
            # Get data to pair mood with
            try:
                latest_data = self.serv._E4_handler.get_data(self.DATA_RANGE)
            except Exception:
                return None
            # Add mood to data
            del latest_data["timestamp"]
            instance = self.serv._E4_model.get_instance(self._convert(latest_data))

            self._save_instance(instance, int(message))


class EstimatedEmotion(Action):
    def __init__(self, frequency, serv):
        super().__init__(frequency, serv)
        self.NAME = "ESTM"
        self.DEVICES = ["E4"]
        self._signal_index = 0
        self.DATA_RANGE = 10
    
    def _convert(self, latest_data):
        ret_dict = {}
        for key, val in latest_data.items():
            ret_dict[key] = np.array(val)
        return ret_dict
    
    def _save_prediction(self, index):
        # Check if csv file already exists
        FILE_NAME = os.path.join(os.path.dirname(__file__), "../Dashboard/assets/emotions.csv")
        df = None

        if os.path.exists(FILE_NAME):
            df = pd.read_csv(FILE_NAME)
        else:
            df = pd.DataFrame({
                "timestamps" : [],
                "emotions" : []
            })
        timestamp = int(time.time())
        df1 = pd.DataFrame({
            "timestamps" : [timestamp],
            "emotions" : [index]
        })
        df = pd.concat([df, df1], ignore_index=True)
        df.to_csv(FILE_NAME, index=False)

    async def _execute(self):
        latest_data = self.serv._E4_handler.get_data(self.DATA_RANGE)

        # Convert to correct format before using with E4Model
        signal_values = self._convert(latest_data)
        # Do stuff
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
        print(await self._msg_client_wait("Tjabba"))


class Test2Action(Action):
    def __init__(self, frequency, serv):
        super().__init__(frequency, serv)
        self.NAME = "TEST2"
        self.ACTIONS = ["TEST"]
        self.DEVICES = ["TEST"]
        self.CLIENT_ACTION = True

class Test3Action(Action):
    def __init__(self, frequency, serv):
        super().__init__(frequency, serv)
        self.NAME = "TEST3"
        self.DEVICES = ["TEST2"]
        

class Test4Action(Action):
    def __init__(self, frequency, serv):
        super().__init__(frequency, serv)
        self.NAME = "TEST4"
        self.ACTIONS = ["TEST3"]
        self.DEVICES = ["TEST2"]
        self.CLIENT_ACTION = True


class StuckAction(Action):
    def __init__(self, frequency, serv):
        super().__init__(frequency, serv)
        self.NAME = "STUCK"
        self.DEVICES = ["EYE"]
        self.xcoords = []
        self.ycoords = []
        self.last_sec = []
    async def _execute(self):
        self.gazetracker = self.serv.eye_tracker.gazetracker
        coordinate = self.gazetracker.get_gaze_position()

        if coordinate[0] is not None and coordinate[1] is not None:
            self.last_sec.append(coordinate)
        if len(self.last_sec) >= 60:
            x_sum = 0
            y_sum = 0
            for coord in self.last_sec:
                x_sum += coord[0]
                y_sum += coord[1]
            coordinate = (x_sum/len(self.last_sec),y_sum/len(self.last_sec))
            self.last_sec = []
            if coordinate[0] is not None: 
                if len(self.xcoords) > 12:
                    self.xcoords.pop(0)
                self.xcoords.append(coordinate[0])
            if coordinate[1] is not None:
                if len(self.ycoords) > 12:
                    self.ycoords.pop(0)
                self.ycoords.append(coordinate[1])
            if len(self.xcoords) > 8:
                stuck = self.gazetracker.stuck_check(min(self.xcoords),max(self.xcoords),min(self.ycoords),max(self.ycoords))
                if stuck is not None:
                    textt = await self._msg_client_wait("hello")
                    


class ActionBreak(Action):
    def __init__(self, frequency, serv):
        super().__init__(frequency, serv)
        self.NAME = "BRK"
        self.DEVICES = ["E4"]
        self.frequency = frequency
        self.percentage = 0.7
        self.emotion = "1"
        self.settings["CERT"] = self._set_certainty
        self.settings["EMO"] = self._set_emotion

    def _set_certainty(self, cert_str):
        changed = True
        try:
            self.percentage = float(cert_str)
        except Exception:
            changed = False
        return changed
    
    def _set_emotion(self, emotion):
        pass

    async def _execute(self):
        # read the last x minutes from the emotions file 
        PATH = "../Dashboard/Sensors/emotions.csv"
        df = pd.read_csv(PATH)
        now = time.time()
        # frequency = 1 / s
        past = now - (1 / self.frequency) # now - s
        df = df[df['timestamps'] > past]
        emotion_values = list(df['emotions'].values)

        stress_count = 0

        for emotion in emotion_values:
            if emotion == 1:
                stress_count += 1

        if stress_count >= len(emotion_values) * self.percentage: # if 70% of the predicted emotions are stressed
            msg = 'take_break'
            await self._msg_client(msg)
        else:
            msg = 'continue_working'
            await self._msg_client(msg)

