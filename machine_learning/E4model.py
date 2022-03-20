import torch
import os

import numpy as np
from .train import Model
import sys
import feature_extraction

dirname = os.path.dirname(os.path.realpath(__file__))
class E4model():
    def __init__(self, baseline_values):
        self.fe = feature_extraction.FeatureExtractor(baseline_values)

        self.arousal_model = Model()
        self.arousal_model.load_state_dict(torch.load(dirname + '/models/arousal.pth'))

        self.valence_model = Model()
        self.valence_model.load_state_dict(torch.load(dirname + '/models/valence.pth'))
        
    def predict(self, signal_values):
        instance = self.fe.create_instance(signal_values)
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


