import json
import os
import time

class DummyE4:

    def __init__(self):
        self.data = {}
        with open(os.path.join(os.path.dirname(__file__),
            "data/fake_data.json")) as f:
            self.data = json.load(f)
    
    def get_data(self, n):
        dataObject = {
                "TEMP": [],
                "HR": [],
                "BVP": [],
                "EDA": [],
                "timestamp": 0
                }
        for i in range(n):
            for j in range(4):
                dataObject["TEMP"].append(self.data["TEMP"][0])
                self.data["TEMP"].append(self.data["TEMP"].pop(0))
            for j in range(64):
                dataObject["BVP"].append(self.data["BVP"][0])
                self.data["BVP"].append(self.data["BVP"].pop(0))
            for j in range(1):
                dataObject["HR"].append(self.data["HR"][0])
                self.data["HR"].append(self.data["HR"].pop(0))
            for j in range(4):
                dataObject["EDA"].append(self.data["EDA"][0])
                self.data["EDA"].append(self.data["EDA"].pop(0))
            dataObject["timestamp"] = time.time()
        return dataObject
