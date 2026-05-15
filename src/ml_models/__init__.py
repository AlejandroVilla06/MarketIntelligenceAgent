"""ML Models Module - Anomaly Detection, Trend Prediction, Forecasting."""

from __future__ import annotations

from .features import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_volume_features,
    FeatureEngineer,
)
from .architecture import AnomalyDetector, TrendPredictor
from .trainers import AnomalyTrainer, TrendTrainer

__all__ = [
    # Features
    "calculate_sma",
    "calculate_ema",
    "calculate_rsi",
    "calculate_macd",
    "calculate_bollinger_bands",
    "calculate_volume_features",
    "FeatureEngineer",
    # Architecture
    "AnomalyDetector",
    "TrendPredictor",
    # Trainers
    "AnomalyTrainer",
    "TrendTrainer",
]