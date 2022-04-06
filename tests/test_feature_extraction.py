from cmath import sin
import pandas as pd
import numpy as np
import os
import sys
import json

sys.path.append('../machine_learning/')

import feature_extraction

def get_signal(df, timestamp, seconds, sample_rate):
    start_of_recording = int(df.columns[0].split('.')[0])
    duration = timestamp - start_of_recording
    end = duration * sample_rate
    start = end - (seconds * sample_rate) + 1
    signal = list(df.iloc[start:end, 0])
    print(signal)
    return signal

def print_test(est, true, name):
    est = np.array(est)
    true = np.array(true)
    print('testing', name)
    print('est:  ', est)
    print('true: ', true)
    error = (np.abs(true - est)).mean()
    print(error)
    print()

# raw signals from participant 22
HR = pd.read_csv('../machine_learning/data/E4/HR.csv')
EDA = pd.read_csv('../machine_learning/data/E4/EDA.csv')
BVP = pd.read_csv('../machine_learning/data/E4/BVP.csv')
TEMP = pd.read_csv('../machine_learning/data/E4/TEMP.csv')

# timestamps where participant 22 were interrupted
df_timestamp = pd.read_csv('../machine_learning/data/times_s22.csv')
interuptions = np.array(df_timestamp.iloc[4:, 1], dtype='int')
end_baseline_timestamp = int(df_timestamp.iloc[2, 1])

# get the true features created in the replication package, participant 22 has id 12
arousal_df = pd.read_csv('../machine_learning/data/SAM_arousal.csv')
df_bool = arousal_df['id'].apply(lambda x: True if 12 == int(str(x).split('.')[0]) else False)
true_features = arousal_df[df_bool]

# 30 second signals with a natural state of mind
baseline_values = {
        "HR": get_signal(HR, end_baseline_timestamp, 30, 1),
        "BVP": get_signal(BVP, end_baseline_timestamp, 30, 64),
        "EDA": get_signal(EDA, end_baseline_timestamp, 30, 4),
        "TEMP": get_signal(TEMP, end_baseline_timestamp, 30, 4)
    }

with open("Baselineout.json","w") as opfile:
    json.dump(baseline_values, opfile, indent=4)


#fe = feature_extraction.FeatureExtractor(baseline_values)

estimated_features = []

# create features from the signal 10 seconds before interruption
signl_lst = []

for timestamp in interuptions:
    signal_values = {
            "HR": get_signal(HR, timestamp, 10, 1),
            "BVP": get_signal(BVP, timestamp, 10, 64),
            "EDA": get_signal(EDA, timestamp, 10, 4),
            "TEMP": get_signal(TEMP, timestamp, 10, 4)
        }
    signl_lst.append(signal_values)
    #instance = fe.create_instance(signal_values)
    #estimated_features.append(instance)

with open("SignalOut.json","w") as opfile:
    json.dump(signl_lst, opfile, indent=4)
print("Tja")
exit(1)
estimated_features_df = pd.DataFrame(estimated_features)
print(estimated_features_df.shape)
print(true_features.head())
print(estimated_features_df.head())

feature_order = [
        'mean_SCL',
        'AUC_Phasic',
        'min_peak_amplitude',
        'max_peak_amplitude',
        'mean_phasic_peak',
        'sum_phasic_peak_amplitude',
        'mean_temp',
        'mean_temp_difference',
        'max_temp',
        'max_temp_difference',
        'min_temp',
        'min_temp_difference',
        'difference_BVPpeaks_ampl',
        'mean_BVPpeaks_ampl',
        'min_BVPpeaks_ampl',
        'max_BVPpeaks_ampl',
        'sum_peak_ampl',
        'HR_mean_difference',
        'HR_variance_difference'
    ]

# compare each feature from the dataset with the calculated features
for i in range(0, 18):
    est = estimated_features_df.iloc[:, i]
    true = true_features[feature_order[i]]

    print_test(est, true, feature_order[i])
     
