import pandas as pd
import numpy as np
import os
import json
import sys
import asyncio
import struct
from VSCServerManager import ServerManager
import time

sys.path.append("../machine_learning")
sys.path.append("../")

import machine_learning


def get_dummy_baselines():
    opfile = open("Baselineout.json","r")
    ret_val = json.load(opfile)
    opfile.close()
    ret_dict = {}
    for key,val in ret_val.items():
        ret_dict[key] = np.array(val)
    return ret_dict

def get_dummy_signalines():
    opfile = open("SignalOut.json","r")
    ret_val = json.load(opfile)
    opfile.close()
    ret_list = []
    for i in ret_val:
        ret_dict = {}
        for key,val in i.items():
            ret_dict[key] = np.array(val)
        ret_list.append(ret_dict)
    return ret_list

def get_pogs():
    EYETRACKER_FREQ = 64
    df = pd.read_csv("27_01_2022_clean.csv")
    df = df[df.index % EYETRACKER_FREQ == 0]
    df = df.reset_index()
    ret = dict(df)
    return ret

class VSCDataHandler:
    def __init__(self, port, frequency = 1):
        self.baseline_values = get_dummy_baselines()
        self.signal_values = get_dummy_signalines()
        self.pogs = get_pogs()
        self.model = machine_learning.E4model(self.baseline_values)
        self.manager = ServerManager(port, frequency)
        self.frequency = frequency
        self.running = True
        self.flags = bytearray(1)
    
    def _to_msg(self, fpogX, fpogY, pred):
        msg = bytearray(struct.pack("f", fpogX))
        msg += bytearray(struct.pack("f", fpogY))
        arousal = 0
        if pred["arousal"]["class"] == "high":
            arousal = 1
        msg += bytearray([arousal])
        msg += bytearray(struct.pack("f", pred["arousal"]["probability"]))
        print(pred["arousal"]["probability"])
        valence = 0
        if pred["valence"]["class"] == "positive":
            valence = 1
        msg += bytearray([valence])
        msg += bytearray(struct.pack("f", pred["valence"]["probability"]))
        print(pred["valence"]["probability"])
        msg += self.flags
        return msg

    def instance(self):
        counter = 0
        eye_counter = 0
        self.manager.start()
        while self.running:
            pred = self.model.predict(self.signal_values[counter])
            fpogX = float(self.pogs["FPOGX"][eye_counter])
            fpogY = float(self.pogs["FPOGY"][eye_counter])
            msg = self._to_msg(fpogX, fpogY, pred)
            eye_counter = (eye_counter+1) % len(self.pogs["FPOGX"])
            counter = (counter +1) % len(self.signal_values)
            self.manager.send(bytes(msg))
            time.sleep(1/self.frequency)
        
        self.manager.exit()

def main(argv):
    if len(argv) != 2:
        print("Invalid argument")
        return None
    try:
        port = int(argv[1])
    except Exception:
        print("Invalid port")
        return None
    servr = VSCDataHandler(port)
    servr.instance()

    

if __name__ == "__main__":
    main(sys.argv)