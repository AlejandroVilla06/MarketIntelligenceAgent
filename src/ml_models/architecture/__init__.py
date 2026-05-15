"""
Architecture Module for ML Models
=================================

Exports model classes for anomaly detection, trend prediction, and LSTM forecasting.

Usage:
    from src.ml_models.architecture import AnomalyDetector, TrendPredictor

    # Anomaly detection
    detector = AnomalyDetector(model_type="isolation_forest")
    detector.train(normal_data_df)
    results = detector.predict(test_data_df)

    # Trend prediction
    predictor = TrendPredictor(n_estimators=100, max_depth=6)
    predictor.train(features_df, labels_series)
    result = predictor.predict(new_data_df)
"""

from __future__ import annotations

from src.ml_models.architecture.anomaly import AnomalyDetector
from src.ml_models.architecture.trend import TrendPredictor

__all__ = [
    "AnomalyDetector",
    "TrendPredictor",
]