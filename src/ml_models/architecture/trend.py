"""
Trend Prediction Module
====================

Uses XGBoost for predicting stock price direction (up/down).

Usage:
    from src.ml_models.architecture import TrendPredictor

    predictor = TrendPredictor(n_estimators=100, max_depth=6)
    metrics = predictor.train(features_df, labels_series)
    results = predictor.predict(new_data_df)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import polars as pl
import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from src.utils import get_logger


# =============================================================================
# LOGGING
# =============================================================================

logger = get_logger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class PredictionResult:
    """
    Result of trend prediction.

    Attributes:
        direction: Predicted price direction ("up" or "down")
        confidence: Confidence score (0.0 to 1.0)
        probability_up: Probability of upward movement
        probability_down: Probability of downward movement
    """

    direction: str
    confidence: float
    probability_up: float
    probability_down: float


# =============================================================================
# TREND PREDICTOR
# =============================================================================


class TrendPredictor:
    """
    Predicts stock price direction (up/down) using XGBoost classifier.

    Uses technical indicators as features to predict whether the price
    will move up or down in the next time period.

    Attributes:
        n_estimators: Number of boosting rounds
        max_depth: Maximum tree depth
        learning_rate: Learning rate for boosting

    Usage:
        >>> from polars import DataFrame
        >>> predictor = TrendPredictor(n_estimators=100, max_depth=6)
        >>> metrics = predictor.train(features_df, labels_series)
        >>> results = predictor.predict(new_data_df)
        >>> results.columns
        ['date', 'close', 'direction', 'confidence', 'probability_up', 'probability_down']
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 6,
        learning_rate: float = 0.1,
    ) -> None:
        """
        Initialize TrendPredictor with configuration parameters.

        Args:
            n_estimators: Number of boosting rounds
            max_depth: Maximum tree depth (controls model complexity)
            learning_rate: Learning rate for boosting (smaller = more conservative)

        Raises:
            ValueError: If parameters are out of valid ranges
        """
        # Validate parameters
        if n_estimators <= 0:
            raise ValueError(f"n_estimators must be positive, got {n_estimators}")
        if max_depth <= 0:
            raise ValueError(f"max_depth must be positive, got {max_depth}")
        if learning_rate <= 0 or learning_rate > 1.0:
            raise ValueError(
                f"learning_rate must be between 0.0 and 1.0, got {learning_rate}"
            )

        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self._model: XGBClassifier | None = None
        self._feature_columns: list[str] | None = None

        logger.info(
            f"TrendPredictor initialized: n_estimators={self.n_estimators}, "
            f"max_depth={self.max_depth}, learning_rate={self.learning_rate}"
        )

    @staticmethod
    def create_labels(close_prices: pl.Series) -> pl.Series:
        """
        Create up/down labels from close price series.

        Creates binary labels where:
        - 1 = price went up (positive change)
        - 0 = price went down or stayed the same

        Args:
            close_prices: Series of close prices

        Returns:
            Series with binary labels (0 or 1)
        """
        changes = close_prices.diff()
        labels = changes.map_elements(
            lambda x: 1 if x is not None and x > 0 else 0,
            return_dtype=pl.Int32,
        )
        return labels.alias("direction")

    def train(self, df: pl.DataFrame, labels: pl.Series) -> dict:
        """
        Train XGBoost classifier on features and labels.

        Args:
            df: DataFrame with numeric features (technical indicators)
            labels: Series with binary labels (0 or 1)

        Returns:
            dict with training metrics:
                - accuracy: Training accuracy
                - precision: Precision score
                - recall: Recall score
                - f1: F1 score
                - n_samples: Number of training samples
                - n_features: Number of features used

        Raises:
            ValueError: If DataFrame is empty or labels mismatch
        """
        # Validate input
        if df.height == 0:
            raise ValueError("Cannot train on empty DataFrame")
        if df.height != len(labels):
            raise ValueError(
                f"DataFrame height ({df.height}) != labels length ({len(labels)})"
            )

        # Select only numeric columns for features
        numeric_cols = [
            col
            for col in df.columns
            if df.schema[col] in (pl.Float64, pl.Float32, pl.Int64, pl.Int32)
        ]

        if len(numeric_cols) == 0:
            raise ValueError("No numeric columns found for training")

        logger.info(
            f"Training TrendPredictor on {df.height} samples with {len(numeric_cols)} features"
        )

        # Store feature columns for prediction
        self._feature_columns = numeric_cols

        # Convert to numpy for sklearn
        features_df = df.select(numeric_cols)

        # Handle NaN/Null values by filling with median
        features_array = features_df.to_numpy()
        col_medians = np.nanmedian(features_array, axis=0)
        for i in range(features_array.shape[1]):
            mask = np.isnan(features_array[:, i])
            features_array[mask, i] = (
                col_medians[i] if not np.isnan(col_medians[i]) else 0.0
            )

        labels_array = labels.to_numpy()

        # Initialize and train model
        self._model = XGBClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            random_state=42,
            eval_metric="logloss",
            n_jobs=-1,
        )

        logger.debug(
            f"Fitting XGBClassifier with n_estimators={self.n_estimators}, "
            f"max_depth={self.max_depth}"
        )
        self._model.fit(features_array, labels_array)

        # Calculate training metrics
        train_pred = self._model.predict(features_array)
        metrics = {
            "accuracy": accuracy_score(labels_array, train_pred),
            "precision": precision_score(labels_array, train_pred, zero_division=0),
            "recall": recall_score(labels_array, train_pred, zero_division=0),
            "f1": f1_score(labels_array, train_pred, zero_division=0),
            "n_samples": len(labels_array),
            "n_features": len(numeric_cols),
        }

        logger.info(
            f"Training complete: accuracy={metrics['accuracy']:.3f}, "
            f"f1={metrics['f1']:.3f}"
        )

        return metrics

    def predict(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Predict price direction.

        Args:
            df: DataFrame with features

        Returns:
            DataFrame with added columns:
                - direction: Predicted direction ("up" or "down")
                - confidence: Confidence score (0.0 to 1.0)
                - probability_up: Probability of upward movement
                - probability_down: Probability of downward movement

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

        logger.info(f"Predicting trend on {df.height} samples")

        # Get features in same order as training
        available_cols = [col for col in self._feature_columns if col in df.columns]
        missing_cols = set(self._feature_columns) - set(available_cols)

        if missing_cols:
            logger.warning(
                f"Missing columns during prediction: {missing_cols}. "
                f"These will be filled with zeros."
            )

        # Prepare features array
        features_array = np.zeros((df.height, len(self._feature_columns)))

        for i, col in enumerate(self._feature_columns):
            if col in df.columns:
                col_data = df.select(col).to_numpy().flatten()
                # Handle NaN values
                mask = np.isnan(col_data)
                col_data[mask] = np.nanmedian(col_data) if not np.all(mask) else 0.0
                features_array[:, i] = col_data

        # Get prediction probabilities
        probs = self._model.predict_proba(features_array)
        prob_down = probs[:, 0]
        prob_up = probs[:, 1]

        # Determine direction and confidence
        directions = ["down" if p <= 0.5 else "up" for p in prob_up]
        confidences = [max(p, 1 - p) for p in prob_up]

        # Add results to DataFrame
        result_df = df.clone()
        result_df = result_df.with_columns([
            pl.Series("direction", directions),
            pl.Series("confidence", confidences),
            pl.Series("probability_up", prob_up),
            pl.Series("probability_down", prob_down),
        ])

        n_up = sum(1 for d in directions if d == "up")
        up_rate = n_up / df.height if df.height > 0 else 0.0
        logger.info(
            f"Prediction complete: {n_up} up predictions ({up_rate:.2%})"
        )

        return result_df

    def get_feature_importance(self) -> list[tuple[str, float]]:
        """
        Get feature importance sorted by score.

        Returns:
            List of (column_name, importance_score) tuples sorted descending

        Raises:
            RuntimeError: If model has not been trained
        """
        if self._model is None:
            raise RuntimeError(
                "Model has not been trained. Call train() before get_feature_importance()."
            )

        importances = self._model.feature_importances_
        sorted_importances = sorted(
            zip(self._feature_columns, importances), key=lambda x: x[1], reverse=True
        )

        logger.debug(f"Top 5 features: {sorted_importances[:5]}")

        return sorted_importances

    def save(self, filepath: str | Path) -> None:
        """
        Save trained model to disk using joblib.

        Saves both the XGBoost model and the feature column configuration.

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

        # Save model data
        model_data = {
            "model": self._model,
            "feature_columns": self._feature_columns,
            "n_estimators": self.n_estimators,
            "max_depth": self.max_depth,
            "learning_rate": self.learning_rate,
        }
        joblib.dump(model_data, filepath)

        logger.info(f"Model saved to {filepath}")

    @classmethod
    def load(cls, filepath: str | Path) -> TrendPredictor:
        """
        Load trained model from disk.

        Args:
            filepath: Path to the saved model

        Returns:
            Loaded TrendPredictor instance with trained model

        Raises:
            FileNotFoundError: If model file does not exist
            ValueError: If saved data is invalid
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Model file not found: {filepath}")

        logger.info(f"Loading model from {filepath}")

        # Load model data
        model_data = joblib.load(filepath)

        # Create instance with loaded config
        instance = cls(
            n_estimators=model_data.get("n_estimators", 100),
            max_depth=model_data.get("max_depth", 6),
            learning_rate=model_data.get("learning_rate", 0.1),
        )

        # Load model and feature columns
        instance._model = model_data["model"]
        instance._feature_columns = model_data["feature_columns"]

        logger.info(
            f"Model loaded: n_estimators={instance.n_estimators}, "
            f"n_features={len(instance._feature_columns)}"
        )

        return instance


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "TrendPredictor",
    "PredictionResult",
]