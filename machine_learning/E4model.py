import torch
import os

import numpy as np
from .train_valence import ValenceModel
from .train_arousal import ArousalModel
import sys
import feature_extraction

dirname = os.path.dirname(os.path.realpath(__file__))
class E4model():
    def __init__(self, baseline_values):
        self.fe = feature_extraction.FeatureExtractor(baseline_values)

        self.arousal_model = ArousalModel()
        self.arousal_model.load_state_dict(torch.load(dirname + '/models/arousal.pth'))

        self.valence_model = ValenceModel()
        self.valence_model.load_state_dict(torch.load(dirname + '/models/valence.pth'))
        
    def predict(self, signal_values):
        instance = self.fe.create_instance(signal_values)
        arousal_prediction = self.arousal_model(torch.tensor(instance, dtype=torch.float32))
        valence_prediction = self.valence_model(torch.tensor(instance, dtype=torch.float32))
        if int(arousal_prediction) == 1:
            arousal_class = 'high'
        else:
            arousal_class = 'low'
            arousal_accuracy = 1 - arousal_prediction

        if int(valence_prediction) == 1:
            valence_class = 'positive'
        else:
            valence_class = 'negative'
            valence_accuracy = 1 - valence_prediction
        return {'arousal': 
                   {'class': arousal_class, 'probability': arousal_prediction.item()}, 
                'valence':
                   {'class': valence_class, 'probability': valence_prediction.item()}}

