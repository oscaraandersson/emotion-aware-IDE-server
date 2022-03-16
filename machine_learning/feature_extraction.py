import numpy as np

def normalize_by_baseline(baseline, signal):
    mean = baseline.mean()
    std = baseline.std()
    normalized_signal = [(value - mean) / std for value in signal]
    return np.array(normalized_signal)



class FeatureExtractor():
    ''' takes in a signal with 10 values and extract features '''
    def __init__(self, baseline):
        self.baseline = baseline
        self.signal = None

    def set_signal(self, signal):
        self.signal = signal
        
    # TEMPERATURE ========================================
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
    def get_HR_mean_difference(self):
        normalized_signal = normalize_by_baseline(self.baseline, self.signal)
        return self.baseline.mean() - normalized_signal.mean()

    def get_HR_variance_difference(self):
        normalized_signal = normalize_by_baseline(self.baseline, self.signal)
        return self.baseline.std() - normalized_signal.std()

    # EDA =================================================
    def get_mean_SCL(self):
        return 0

    def get_AUC_Phasic(self):
        return 0

    def get_min_peak_amplitude(self):
        return 0

    def get_max_peak_amplitude(self):
        return 0

    def get_mean_phasic_peak(self):
        return 0

    def get_sum_phasic_peak_amplitude(self):
        return 0

    # BVP ===============================================
    def get_difference_BVPpeaks_ampl(self):
        return 0

    def get_mean_BVPpeaks_ampl(self):
        return 0

    def get_min_BVPpeaks_ampl(self):
        return 0

    def get_max_BVPpeaks_ampl(self):
        return 0

    def get_sum_peak_ampl(self):
        return 0
