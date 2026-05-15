"""
Anomaly Detection Module
========================

Uses Isolation Forest for detecting anomalies in stock market data.

Usage:
    from src.ml_models.architecture import AnomalyDetector

    detector = AnomalyDetector(model_type="isolation_forest")
    detector.train(normal_data_df)
    results = detector.predict(test_data_df)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import polars as pl
from polars import DataFrame
from sklearn.ensemble import IsolationForest

from src.utils import get_logger


# =============================================================================
# LOGGING
# =============================================================================

logger = get_logger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class AnomalyResult:
    """
    Result of anomaly detection prediction.

    Attributes:
        anomaly_score: Isolation Forest score (negative = more anomalous)
        is_anomaly: Boolean indicating if sample is an anomaly
    """

    anomaly_score: float
    is_anomaly: bool


# =============================================================================
# ANOMALY DETECTOR
# =============================================================================


class AnomalyDetector:
    """
    Detects anomalies in stock price/volume data using Isolation Forest.

    The Isolation Forest algorithm isolates anomalies by randomly selecting
    a feature and splitting values. Anomalies require fewer splits to be
    isolated, resulting in lower anomaly scores.

    Attributes:
        model_type: Type of model to use (currently only "isolation_forest")
        n_estimators: Number of trees in the forest
        contamination: Expected proportion of anomalies in data
        max_samples: Number of samples to use for training
        anomaly_threshold: Threshold for is_anomaly decision

    Usage:
        >>> from polars import DataFrame
        >>> detector = AnomalyDetector(model_type="isolation_forest")
        >>> detector.train(normal_data_df)
        {'n_samples': 1000, 'n_features': 12, 'status': 'trained'}
        >>> results = detector.predict(test_data_df)
        >>> results.columns
        ['date', 'close', 'volume', 'anomaly_score', 'is_anomaly']
    """

    SUPPORTED_MODELS = {"isolation_forest"}

    def __init__(
        self,
        model_type: str = "isolation_forest",
        n_estimators: int = 100,
        contamination: float = 0.1,
        max_samples: str = "auto",
        anomaly_threshold: float = 0.5,
    ) -> None:
        """
        Initialize AnomalyDetector with configuration parameters.

        Args:
            model_type: Model type to use (only "isolation_forest" supported)
            n_estimators: Number of trees in the Isolation Forest
            contamination: Proportion of anomalies expected (0.0 to 0.5)
            max_samples: Number of samples to draw for training
            anomaly_threshold: Score threshold for anomaly classification

        Raises:
            ValueError: If model_type is not supported
            ValueError: If parameters are out of valid ranges
        """
        # Validate model type
        if model_type not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported model type: {model_type}. "
                f"Supported types: {self.SUPPORTED_MODELS}"
            )

        # Validate parameters
        if n_estimators <= 0:
            raise ValueError(f"n_estimators must be positive, got {n_estimators}")
        if not 0.0 <= contamination <= 0.5:
            raise ValueError(
                f"contamination must be between 0.0 and 0.5, got {contamination}"
            )
        if anomaly_threshold < 0.0 or anomaly_threshold > 1.0:
            raise ValueError(
                f"anomaly_threshold must be between 0.0 and 1.0, got {anomaly_threshold}"
            )

        self.model_type = model_type
        self.n_estimators = n_estimators
        self.contamination = contamination
        self.max_samples = max_samples
        self.anomaly_threshold = anomaly_threshold
        self._model: IsolationForest | None = None
        self._feature_columns: list[str] | None = None

        logger.info(
            f"AnomalyDetector initialized: model={self.model_type}, "
            f"n_estimators={self.n_estimators}, contamination={self.contamination}, "
            f"anomaly_threshold={self.anomaly_threshold}"
        )

    def train(self, df: pl.DataFrame) -> dict:
        """
        Train on normal (non-anomalous) data.

        The model learns the pattern of normal data and will flag deviations
        as anomalies during prediction.

        Args:
            df: DataFrame with features (technical indicators from FeatureEngineer)

        Returns:
            dict with training metrics:
                - n_samples: Number of training samples
                - n_features: Number of features used
                - feature_columns: List of feature column names
                - status: Training status

        Raises:
            ValueError: If DataFrame is empty or has insufficient data
        """
        # Validate input
        if df.height == 0:
            raise ValueError("Cannot train on empty DataFrame")

        # Select only numeric columns for features
        numeric_cols = [
            col for col in df.columns
            if df.schema[col] in (pl.Float64, pl.Float32, pl.Int64, pl.Int32)
        ]

        if len(numeric_cols) == 0:
            raise ValueError("No numeric columns found for training")

        logger.info(f"Training AnomalyDetector on {df.height} samples with {len(numeric_cols)} features")

        # Store feature columns for prediction
        self._feature_columns = numeric_cols

        # Convert to numpy for sklearn
        features_df = df.select(numeric_cols)

        # Handle NaN/Null values by filling with median
        import numpy as np
        features_array = features_df.to_numpy()
        # Replace NaN with column median
        col_medians = np.nanmedian(features_array, axis=0)
        for i in range(features_array.shape[1]):
            mask = np.isnan(features_array[:, i])
            features_array[mask, i] = col_medians[i] if not np.isnan(col_medians[i]) else 0.0

        # Initialize and train model
        self._model = IsolationForest(
            n_estimators=self.n_estimators,
            contamination=self.contamination,
            max_samples=self.max_samples if self.max_samples != "auto" else df.height,
            random_state=42,
            n_jobs=-1,
        )

        logger.debug(f"Fitting IsolationForest with n_estimators={self.n_estimators}")
        self._model.fit(features_array)

        metrics = {
            "n_samples": df.height,
            "n_features": len(numeric_cols),
            "feature_columns": numeric_cols,
            "status": "trained",
        }

        logger.info(
            f"Training complete: {metrics['n_samples']} samples, "
            f"{metrics['n_features']} features"
        )

        return metrics

    def predict(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Detect anomalies in data.

        Uses the trained model to score each sample. Samples with scores
        below the anomaly_threshold are flagged as anomalies.

        Args:
            df: DataFrame with features

        Returns:
            DataFrame with added columns:
                - anomaly_score: Float score (lower = more anomalous)
                - is_anomaly: Boolean flag

        Raises:
            RuntimeError: If model has not been trained
            ValueError: If DataFrame is empty
        """
        if self._model is None:
            raise RuntimeError(
                "Model has not been trained. Call train() before predict()."
            )

        if df.height == 0:
            raise ValueError("Cannot predict on empty DataFrame")

        if self._feature_columns is None:
            raise RuntimeError("Feature columns not set. Train the model first.")

        logger.info(f"Predicting anomalies on {df.height} samples")

        # Get features in same order as training
        available_cols = [col for col in self._feature_columns if col in df.columns]
        missing_cols = set(self._feature_columns) - set(available_cols)

        if missing_cols:
            logger.warning(
                f"Missing columns during prediction: {missing_cols}. "
                f"These will be filled with zeros."
            )

        # Select and prepare features
        import numpy as np

        # Start with zeros for missing columns
        features_array = np.zeros((df.height, len(self._feature_columns)))

        for i, col in enumerate(self._feature_columns):
            if col in df.columns:
                col_data = df.select(col).to_numpy().flatten()
                # Handle NaN values
                mask = np.isnan(col_data)
                col_data[mask] = np.nanmedian(col_data) if not np.all(mask) else 0.0
                features_array[:, i] = col_data

        # Get anomaly scores
        scores = self._model.score_samples(features_array)
        decision_scores = self._model.decision_function(features_array)

        # Determine anomalies based on threshold
        # Note: sklearn's score_samples returns higher values for normal points
        # We use decision_function which returns higher values for normal points
        is_anomaly = decision_scores < self.anomaly_threshold

        # Add results to DataFrame
        result_df = df.clone()
        result_df = result_df.with_columns([
            pl.Series("anomaly_score", scores),
            pl.Series("is_anomaly", is_anomaly),
        ])

        n_anomalies = sum(is_anomaly)
        anomaly_rate = n_anomalies / df.height if df.height > 0 else 0.0
        logger.info(
            f"Prediction complete: {n_anomalies} anomalies detected "
            f"({anomaly_rate:.2%} anomaly rate)"
        )

        return result_df

    def save(self, filepath: str) -> None:
        """
        Save trained model to disk using joblib.

        Saves both the sklearn model and the detector configuration.

        Args:
            filepath: Path to save the model (without extension)

        Raises:
            RuntimeError: If model has not been trained
            OSError: If file cannot be written
        """
        if self._model is None:
            raise RuntimeError(
                "Cannot save untrained model. Train the model first."
            )

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Save model with joblib
        model_path = filepath.with_suffix(".joblib")
        joblib.dump(self._model, model_path)

        # Save configuration separately
        config = {
            "model_type": self.model_type,
            "n_estimators": self.n_estimators,
            "contamination": self.contamination,
            "max_samples": self.max_samples,
            "anomaly_threshold": self.anomaly_threshold,
            "feature_columns": self._feature_columns,
        }
        config_path = filepath.with_suffix(".config.joblib")
        joblib.dump(config, config_path)

        logger.info(f"Model saved to {model_path} and config to {config_path}")

    @classmethod
    def load(cls, filepath: str) -> AnomalyDetector:
        """
        Load trained model from disk.

        Args:
            filepath: Path to the saved model (without extension)

        Returns:
            Loaded AnomalyDetector instance with trained model

        Raises:
            FileNotFoundError: If model files do not exist
            ValueError: If saved data is invalid
        """
        filepath = Path(filepath)

        if not filepath.with_suffix(".joblib").exists():
            raise FileNotFoundError(f"Model file not found: {filepath}.joblib")
        if not filepath.with_suffix(".config.joblib").exists():
            raise FileNotFoundError(f"Config file not found: {filepath}.config.joblib")

        logger.info(f"Loading model from {filepath}")

        # Load configuration
        config_path = filepath.with_suffix(".config.joblib")
        config = joblib.load(config_path)

        # Create instance with loaded config
        instance = cls(
            model_type=config["model_type"],
            n_estimators=config["n_estimators"],
            contamination=config["contamination"],
            max_samples=config["max_samples"],
            anomaly_threshold=config["anomaly_threshold"],
        )

        # Load model
        model_path = filepath.with_suffix(".joblib")
        instance._model = joblib.load(model_path)
        instance._feature_columns = config["feature_columns"]

        logger.info(
            f"Model loaded: {instance.model_type}, "
            f"n_estimators={instance.n_estimators}"
        )

        return instance


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "AnomalyDetector",
    "AnomalyResult",
]