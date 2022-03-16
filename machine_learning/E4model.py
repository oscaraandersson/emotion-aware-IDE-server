import torch

import numpy as np
from feature_extraction import FeatureExtractor
from train import Model

class E4model():
    def __init__(self, baseline):
        self.fe = FeatureExtractor(baseline)

        self.arousal_model = Model()
        self.arousal_model.load_state_dict(torch.load('models/arousal.pth'))

        self.valence_model = Model()
        self.valence_model.load_state_dict(torch.load('models/valence.pth'))

    def create_instance(self, HR, EDA, TEMP, BVP):
        # creating an instance form 10 seconds of raw data
        instance = []
                         
        self.fe.set_signal(EDA)
        instance.append(self.fe.get_mean_SCL())
        instance.append(self.fe.get_AUC_Phasic())
        instance.append(self.fe.get_min_peak_amplitude())
        instance.append(self.fe.get_max_peak_amplitude())
        instance.append(self.fe.get_mean_phasic_peak())
        instance.append(self.fe.get_sum_phasic_peak_amplitude())
        
        self.fe.set_signal(TEMP)
        instance.append(self.fe.get_mean_temp())
        instance.append(self.fe.get_mean_temp_difference())
        instance.append(self.fe.get_max_temp())
        instance.append(self.fe.get_max_temp_difference())
        instance.append(self.fe.get_min_temp())
        instance.append(self.fe.get_min_temp_difference())

        self.fe.set_signal(BVP)
        instance.append(self.fe.get_difference_BVPpeaks_ampl())
        instance.append(self.fe.get_mean_BVPpeaks_ampl())
        instance.append(self.fe.get_min_BVPpeaks_ampl())
        instance.append(self.fe.get_max_BVPpeaks_ampl())
        instance.append(self.fe.get_sum_peak_ampl())

        self.fe.set_signal(HR)
        instance.append(self.fe.get_HR_mean_difference())
        instance.append(self.fe.get_HR_variance_difference())

        return instance
    
        
    def predict(self, instance):
        arousal_prediction = self.arousal_model(torch.tensor(instance, dtype=torch.float32))
        valence_prediction = self.valence_model(torch.tensor(instance, dtype=torch.float32))
        if int(arousal_prediction) == 1:
            arousal_class = 'high'
        else:
            arousal_class = 'low'

        if int(valence_prediction) == 1:
            valence_class = 'positive'
        else:
            valence_class = 'negative'
        return {'arousal': 
                   {'class': arousal_class, 'probability': arousal_prediction.item()}, 
                'valence':
                   {'class': valence_class, 'probability': valence_prediction.item()}}


