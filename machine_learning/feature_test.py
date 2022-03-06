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

def print_test(feature_dict, true_features):
    for key, value in feature_dict.items():
        print(mean_squared_error_test(feature_dict[key], true_features[key]), ':', key)
    print()

def test_temp(true_features, baseline_timestamp, interuptions):
    temp_df = pd.read_csv('data/E4/TEMP.csv')
    baseline = get_signal(temp_df, baseline_timestamp, 30, 4)
    fe = FeatureExtractor(baseline)
    
    feature_dict = {
                'mean_temp': [],
                'mean_temp_difference': [],
                'max_temp': [],
                'max_temp_difference': [],
                'min_temp': [],
                'min_temp_difference': []
            }

    for timestamp in interuptions:
        signal = get_signal(temp_df, timestamp, 10, 4)
        fe.set_signal(signal)
        
        feature_dict['mean_temp'].append(fe.get_mean_temp())
        feature_dict['mean_temp_difference'].append(fe.get_mean_temp_difference())
        feature_dict['max_temp'].append(fe.get_max_temp())
        feature_dict['max_temp_difference'].append(fe.get_max_temp_difference())
        feature_dict['min_temp'].append(fe.get_min_temp())
        feature_dict['min_temp_difference'].append(fe.get_min_temp_difference())

    print('Testing TEMP')
    print_test(feature_dict, true_features)


def test_HR(ture_features, baseline_timestamp, interuptions):
    hr_df = pd.read_csv('data/E4/HR.csv')
    baseline = get_signal(hr_df, baseline_timestamp, 30, 1)
    fe = FeatureExtractor(baseline)
    
    HR_mean_difference, HR_variance_difference = [], []
    feature_dict = {
            'HR_mean_difference': [],
            'HR_variance_difference': []
        }

    for timestamp in interuptions:
        signal = get_signal(hr_df, timestamp, 10, 1)
        fe.set_signal(signal)
        
        feature_dict['HR_mean_difference'].append(fe.get_mean_temp())
        feature_dict['HR_variance_difference'].append(fe.get_mean_temp_difference())

    print('Testing HR') 
    print_test(feature_dict, true_features) 


def test_BVP(ture_features, baseline_timestamp, interuptions):
    df = pd.read_csv('data/E4/BVP.csv')
    baseline = get_signal(df, baseline_timestamp, 30, 64)
    fe = FeatureExtractor(baseline)
    
    feature_dict = {
            'difference_BVPpeaks_ampl': [],
            'mean_BVPpeaks_ampl': [],
            'min_BVPpeaks_ampl': [],
            'max_BVPpeaks_ampl': [],
            'sum_peak_ampl': []
        }

    for timestamp in interuptions:
        signal = get_signal(df, timestamp, 10, 64)
        fe.set_signal(signal)
        
        feature_dict['difference_BVPpeaks_ampl'].append(fe.get_difference_BVPpeaks_ampl())
        feature_dict['mean_BVPpeaks_ampl'].append(fe.get_mean_BVPpeaks_ampl())
        feature_dict['min_BVPpeaks_ampl'].append(fe.get_min_BVPpeaks_ampl())
        feature_dict['max_BVPpeaks_ampl'].append(fe.get_max_BVPpeaks_ampl())
        feature_dict['sum_peak_ampl'].append(fe.get_sum_peak_ampl())

    print('Testing BVP')
    print_test(feature_dict, true_features)

def test_EDA(ture_features, baseline_timestamp, interuptions):
    df = pd.read_csv('data/E4/EDA.csv')
    baseline = get_signal(df, baseline_timestamp, 30, 4)
    fe = FeatureExtractor(baseline)
    
    feature_dict = {
            'mean_SCL': [],
            'AUC_Phasic': [],
            'min_peak_amplitude': [],
            'max_peak_amplitude': [],
            'mean_phasic_peak': [],
            'sum_phasic_peak_amplitude': []
        }

    for timestamp in interuptions:
        signal = get_signal(df, timestamp, 10, 4)
        fe.set_signal(signal)
        
        feature_dict['mean_SCL'].append(fe.get_mean_SCL())
        feature_dict['AUC_Phasic'].append(fe.get_AUC_Phasic())
        feature_dict['min_peak_amplitude'].append(fe.get_min_peak_amplitude())
        feature_dict['max_peak_amplitude'].append(fe.get_max_peak_amplitude())
        feature_dict['mean_phasic_peak'].append(fe.get_mean_phasic_peak())
        feature_dict['sum_phasic_peak_amplitude'].append(fe.get_sum_phasic_peak_amplitude())

    print('Testing EDA') 
    print_test(feature_dict, true_features)

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
    test_BVP(true_features, end_baseline_timestamp, interuptions)
    test_EDA(true_features, end_baseline_timestamp, interuptions)
    
     


