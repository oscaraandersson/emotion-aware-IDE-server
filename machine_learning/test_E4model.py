from E4model import E4model
import pandas as pd
import numpy as np
import random

baseline = np.array([random.randrange(60, 70) for _ in range(0, 30)])
model = E4model(baseline)

HR = pd.read_csv('data/E4/HR.csv')
TEMP = pd.read_csv('data/E4/TEMP.csv')
BVP = pd.read_csv('data/E4/BVP.csv')
EDA = pd.read_csv('data/E4/EDA.csv')

def get_values(df, f):
    return df.iloc[100:100 + f*10, 0]

instance = model.create_instance(get_values(HR, 1), get_values(TEMP, 4), get_values(BVP, 64), get_values(EDA, 4))
pred = model.predict(instance)
print(pred)

