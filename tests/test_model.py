import unittest
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib

class TestModel(unittest.TestCase):
    def test_model_prediction(self):
        model = joblib.load('models/stock_model.pkl')
        features = np.array([[100, 101, 99, 5000, 0.01, 0.02, 99, 101, 50, 100, 0.5]])
        pred = model.predict(features)
        self.assertTrue(isinstance(pred[0], float))
        self.assertGreaterEqual(pred[0], 0)

if __name__ == '__main__':
    unittest.main()