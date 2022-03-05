import pandas as pd
import numpy as np
import os

from feature_extraction import FeatureExtractor

def get_signal(df, timestamp, seconds, sample_rate):
    start_of_recording = int(df.columns[0].split('.')[0])
    duration = timestamp - start_of_recording
    end = duration * sample_rate
    start = end - (seconds * sample_rate)
    signal = np.array(df.iloc[start:end, 0])
    return signal


def mean_squared_error_test(features, true_features):
    features = np.array(features)
    true_features = np.array(true_features)
    err = (np.square(true_features) - np.square(features)).mean()
    if err < 0.01:
        return 'pass'
    else:
        return 'fail'

def test_temp(true_features, baseline_timestamp, interuptions):
    temp_df = pd.read_csv('data/E4/TEMP.csv')
    baseline = get_signal(temp_df, baseline_timestamp, 30, 4)
    fe = FeatureExtractor(baseline)
    
    mean_temp, mean_temp_difference  = [], []
    max_temp, max_temp_difference  = [], []
    min_temp, min_temp_difference  = [], []

    for timestamp in interuptions:
        signal = get_signal(temp_df, timestamp, 10, 4)
        fe.set_signal(signal)
        
        mean_temp.append(fe.get_mean_temp())
        mean_temp_difference.append(fe.get_mean_temp_difference())
        
        max_temp.append(fe.get_max_temp())
        max_temp_difference.append(fe.get_max_temp_difference())
        
        min_temp.append(fe.get_min_temp())
        min_temp_difference.append(fe.get_min_temp_difference())

    # pass determined if the mean squared error is less than 0.01
    print('testing temperature data')
    print(f"mean_temp: {mean_squared_error_test(mean_temp, true_features['mean_temp'])}")
    print(f"mean_temp_difference: {mean_squared_error_test(mean_temp_difference, true_features['mean_temp_difference'])}")
    print()
    print(f"max_temp: {mean_squared_error_test(max_temp, true_features['max_temp'])}")
    print(f"max_temp_difference: {mean_squared_error_test(max_temp_difference, true_features['max_temp_difference'])}")
    print()
    print(f"min_temp: {mean_squared_error_test(min_temp, true_features['min_temp'])}")
    print(f"min_temp_difference: {mean_squared_error_test(min_temp_difference, true_features['min_temp_difference'])}")
    print()

def test_HR(ture_features, baseline_timestamp, interuptions):
    hr_df = pd.read_csv('data/E4/HR.csv')
    baseline = get_signal(hr_df, baseline_timestamp, 30, 1)
    fe = FeatureExtractor(baseline)
    
    HR_mean_difference, HR_variance_difference = [], []

    for timestamp in interuptions:
        signal = get_signal(hr_df, timestamp, 10, 1)
        fe.set_signal(signal)
        
        HR_mean_difference.append(fe.get_mean_temp())
        HR_variance_difference.append(fe.get_mean_temp_difference())

    print('Testing heartreate data')
    print(f"HR_mean_differene: {mean_squared_error_test(HR_mean_difference, true_features['HR_mean_difference'])}")
    print(f"HR_variance_differene: {mean_squared_error_test(HR_variance_difference, true_features['HR_variance_difference'])}")
    


if __name__ == '__main__':
    # file with timestamps to get the data used to create features
    df_timestamp = pd.read_csv('data/times_s22.csv')
    interuptions = np.array(df_timestamp.iloc[4:, 1], dtype='int')
    end_baseline_timestamp = int(df_timestamp.iloc[2, 1])

    # get the true features created in the replication package, participant 22 has id 12
    arousal_df = pd.read_csv('data/SAM_arousal.csv')
    df_bool = arousal_df['id'].apply(lambda x: True if 12 == int(str(x).split('.')[0]) else False)
    true_features = arousal_df[df_bool]
    
    test_temp(true_features, end_baseline_timestamp, interuptions)
    test_HR(true_features, end_baseline_timestamp, interuptions)
     


