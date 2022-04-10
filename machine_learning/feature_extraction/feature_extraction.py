import numpy as np
import pandas as pd

# libraries for extracting the EDA signal
# cvxEDA is the original package but is unable to build on ARM
from .kvxEDA import kvxEDA
from .kbk_scr import kbk_scr

# libraries for BVP preprocessing
from scipy.signal import butter, lfilter
from pyampd.ampd import find_peaks


class FeatureExtractor():

    ''' Class for converting signals from the E4 wristband to useful features
    It requires a 30 second reccording with baseline signals from each source,
    this reccording should reflect a natural state of mind

    create_instance() returns a 19 element list with features, that can be 
    used for inference
    '''

    def __init__(self, baseline_values):
        self.HR_baseline = baseline_values['HR']
        self.BVP_baseline = baseline_values['BVP']
        self.EDA_baseline = baseline_values['EDA']
        self.TEMP_baseline = baseline_values['TEMP']

    def set_signal(self, signal):
        self.signal = signal

    def set_baseline(self, baseline):
        self.baseline = baseline

    def normalize_by_baseline(self, baseline, signal):
        mean = baseline.mean()
        std = baseline.std()
        normalized_signal = [(value - mean) / std for value in signal]
        return np.array(normalized_signal)
        
    def create_instance(self, signals):
        # unpacking signals
        HR = signals['HR']
        BVP = signals['BVP']
        EDA = signals['EDA']
        TEMP = signals['TEMP']

        self.set_signal(HR)
        self.set_baseline(self.HR_baseline)
        HR_features = self.get_HR_features()

        self.set_signal(BVP)
        self.set_baseline(self.BVP_baseline)
        BVP_features = self.get_BVP_features()

        self.set_signal(EDA)
        self.set_baseline(self.EDA_baseline)
        EDA_features = self.get_EDA_features()

        self.set_signal(TEMP)
        self.set_baseline(self.TEMP_baseline)
        TEMP_features = self.get_TEMP_features()

        # all features, might be in worng order
        features = {**HR_features, **BVP_features, **EDA_features, **TEMP_features}

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

        instance = []

        # the features shold be in a specefic order for the machinelarning inference to work
        for name in feature_order:
            instance.append(features[name])
        
        return instance
            

    # TEMPERATURE ========================================
    def get_TEMP_features(self):
        features = {
                'mean_temp': self.get_mean_temp(),
                'mean_temp_difference': self.get_mean_temp_difference(),
                'max_temp': self.get_max_temp(),
                'max_temp_difference': self.get_max_temp_difference(),
                'min_temp': self.get_min_temp(),
                'min_temp_difference': self.get_min_temp_difference()
            }

        return features

    def get_mean_temp(self):
        return self.signal.mean()

    def get_mean_temp_difference(self):
        return self.baseline.min() - self.signal.min()

    def get_max_temp(self):
        return self.signal.max()

    def get_max_temp_difference(self):
        return self.baseline.max() - self.signal.max()

    def get_min_temp(self):
        return self.signal.min()

    def get_min_temp_difference(self):
        return self.baseline.min() - self.signal.min()

    # HERTRATE ============================================
    def get_HR_features(self):
        features = {
                'HR_mean_difference': self.get_HR_mean_difference(),
                'HR_variance_difference': self.get_HR_variance_difference()
            }
        
        return features

    def get_HR_mean_difference(self):
        return self.baseline.mean() - self.signal.mean()

    def get_HR_variance_difference(self):
        return self.baseline.var() - self.signal.var()

    # EDA =================================================
    def get_EDA_features(self):
        signal = self.normalize_by_baseline(self.baseline, self.signal)
        ret = kvxEDA(signal, 1/4)
        self.tonic = ret.tonic
        self.phasic = ret.phasic
        self.scr_signal = kbk_scr(signal=self.phasic, sampling_rate=4, min_amplitude=0.1)

        features = {
                'mean_SCL': self.get_mean_SCL(),
                'AUC_Phasic': self.get_AUC_Phasic(),
                'min_peak_amplitude': self.get_min_peak_amplitude(),
                'max_peak_amplitude': self.get_max_peak_amplitude(),
                'mean_phasic_peak': self.get_mean_phasic_peak(),
                'sum_phasic_peak_amplitude': self.get_mean_phasic_peak()
            }

        return features

    def get_mean_SCL(self):
        return np.mean(self.tonic)

    def get_AUC_Phasic(self):
        return np.trapz(self.phasic, dx=1/4) 

    def get_min_peak_amplitude(self):
        amplitudes = self.scr_signal.amplitudes
        if len(amplitudes) > 0:
            return min(amplitudes)
        else:
            return 0

    def get_max_peak_amplitude(self):
        amplitudes = self.scr_signal.amplitudes
        if len(amplitudes) > 0:
            return max(amplitudes)
        else:
            return 0

    def get_mean_phasic_peak(self):
        amplitudes = self.scr_signal.amplitudes
        if len(amplitudes) > 0:
            return amplitudes.mean()
        else:
            return 0

    def get_sum_phasic_peak_amplitude(self):
        amplitudes = self.scr_signal.amplitudes
        if len(amplitudes) > 0:
            return amplitudes.sum()
        else:
            return 0

    # BVP ===============================================
    def get_BVP_features(self):
        b, a = butter(2, Wn=[1/1000, 8/1000], btype='pass')

        self.BVP_normalized = self.normalize_by_baseline(self.baseline, self.signal)
        self.BVP_preprocessed = lfilter(b, a, self.signal)
        self.baseline_preprocessed = lfilter(b, a, self.baseline)

        if (self.BVP_preprocessed.shape != 0):
            try:
                self.peaks_signal = find_peaks(self.BVP_preprocessed)
            except:
                self.peaks_signal = [0]
        else:
            self.peaks_signal = [0]
        if (self.baseline_preprocessed.shape != 0):
            self.peaks_baseline = find_peaks(self.baseline_preprocessed)
        else:
            self.peaks_baseline = [0]
        if (self.BVP_normalized.shape != 0):
            self.peaks_normalized = find_peaks(self.BVP_normalized)
        else:
            self.peaks_normalized = [0]

        features = {
                'difference_BVPpeaks_ampl': self.get_difference_BVPpeaks_ampl(),
                'mean_BVPpeaks_ampl': self.get_mean_BVPpeaks_ampl(self.BVP_normalized, self.peaks_normalized),
                'min_BVPpeaks_ampl': self.get_min_BVPpeaks_ampl(),
                'max_BVPpeaks_ampl': self.get_max_BVPpeaks_ampl(),
                'sum_peak_ampl': self.get_sum_peak_ampl()
            }

        return features


    def get_difference_BVPpeaks_ampl(self):
        BVP_peak_amplitude_baseline = self.get_mean_BVPpeaks_ampl(self.baseline_preprocessed, self.peaks_baseline)
        BVP_peak_amplitude_signal = self.get_mean_BVPpeaks_ampl(self.BVP_preprocessed, self.peaks_signal)
        return BVP_peak_amplitude_baseline - BVP_peak_amplitude_signal

    def get_mean_BVPpeaks_ampl(self, BVP_normalized, peaks_normalized):
        s = 0
        mean = 0
        l = len(peaks_normalized)
        for i in range(0, l):
            s += BVP_normalized[peaks_normalized[i]]
        if (l == 0):
            return 0
        return s/l

    def get_min_BVPpeaks_ampl(self):
        amplitudes = []
        l = len(self.peaks_normalized)
        for i in range(0, l):
            amplitudes.append(self.BVP_normalized[self.peaks_normalized[i]])
        if (l == 0):
            return 0
        return min(amplitudes)

    def get_max_BVPpeaks_ampl(self):
        amplitudes = []
        l = len(self.peaks_normalized)
        for i in range(0, l):
            amplitudes.append(self.BVP_normalized[self.peaks_normalized[i]])
        if (l == 0):
            return 0
        return max(amplitudes)

    def get_sum_peak_ampl(self):
        s = 0
        l = len(self.peaks_normalized)
        for i in range(0, l):
            s += self.BVP_normalized[self.peaks_normalized[i]]
        return s 
