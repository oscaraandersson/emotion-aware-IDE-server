import sys
sys.path.append('../')
sys.path.append('../machine_learning/')

import machine_learning
import pandas as pd
import numpy as np
import random


HR = pd.read_csv('../machine_learning/data/E4/HR.csv')
TEMP = pd.read_csv('../machine_learning/data/E4/TEMP.csv')
BVP = pd.read_csv('../machine_learning/data/E4/BVP.csv')
EDA = pd.read_csv('../machine_learning/data/E4/EDA.csv')

def get_values(df, Hz, seconds, start):
    return df.iloc[Hz*start:Hz*start + Hz*seconds, 0]


baseline_values = {
        'HR': get_values(HR, 1, 30, 500),
        'TEMP': get_values(TEMP, 4, 30, 500),
        'BVP': get_values(BVP, 64, 30, 500),
        'EDA': get_values(EDA, 4, 30, 500)
    }

signal_values = {
        'HR': get_values(HR, 1, 10, 1000),
        'TEMP': get_values(TEMP, 4, 10, 1000),
        'BVP': get_values(BVP, 64, 10, 1000),
        'EDA': get_values(EDA, 4, 10, 1000)
    }

model = machine_learning.E4model(baseline_values)
pred = model.predict(signal_values)
print(pred)

