import torch
import os
import sys

import numpy as np
from .train_multiclass import Model
import feature_extraction
from joblib import load

dirname = os.path.dirname(os.path.realpath(__file__))
class E4model():
    def __init__(self, baseline_values):
        self.fe = feature_extraction.FeatureExtractor(baseline_values)

        self.model = Model()
        self.model.load_state_dict(torch.load(dirname + '/models/emotion_classifier.pth'))

    # [1, 0, 0, 0] : high, negative 
    # [0, 1, 0, 0] : high, positive 
    # [0, 0, 1, 0] : low, negative
    # [0, 0, 0, 1] : low, positive 

    # example prediction will look like:
    # [0.0025, 0.7988, 0.0924, 0.0667]
    # where numbers represent certainty -> first quadrant of the circle with 80% certainty

    def get_instance(self, signal_values):
        return self.fe.create_instance(signal_values)

    def predict(self, signal_values):
        sc = load(dirname + '/scaler.joblib')
        instance = sc.transform(np.array([self.get_instance(signal_values)]))
        prediction = (self.model(torch.tensor(instance, dtype=torch.float32)))
        ret = prediction.tolist()[0]
        return ret 

