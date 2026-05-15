"""
Trend Prediction Trainer
======================

Orchestrates training workflow for trend prediction with TimeSeriesSplit.

Usage:
    from src.ml_models.trainers import TrendTrainer

    trainer = TrendTrainer()
    df = trainer.load_data(symbols=["AAPL"])
    df_features = trainer.prepare_features(df)
    labels = trainer.create_labels(df_features)

    metrics = trainer.train(df_features, labels)
    print(f"CV F1: {metrics['cv_f1_mean']:.3f} +/- {metrics['cv_f1_std']:.3f}")
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import polars as pl
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)

from src.utils import get_logger

if TYPE_CHECKING:
    from src.ml_models.architecture.trend import TrendPredictor


# =============================================================================
# LOGGING
# =============================================================================

logger = get_logger(__name__)


# =============================================================================
# TREND TRAINER
# =============================================================================


class TrendTrainer:
    """
    Handles loading data, feature engineering, label creation,
    training, and evaluation for trend prediction.

    Responsibilities:
    - Load processed stock data
    - Apply technical indicator feature engineering
    - Create up/down labels from price movements
    - Train XGBoost classifier with TimeSeriesSplit CV
    - Evaluate model performance

    Usage:
        trainer = TrendTrainer()
        df = trainer.load_data(symbols=["AAPL"])
        df_features = trainer.prepare_features(df)
        labels = trainer.create_labels(df_features)

        metrics = trainer.train(df_features, labels)
        print(f"CV F1: {metrics['cv_f1_mean']:.3f}")
    """

    def __init__(
        self,
        data_dir: str | Path = "data/processed/stocks",
        model_dir: str | Path = "src/ml_models/saved",
    ) -> None:
        """
        Initialize TrendTrainer with directories.

        Args:
            data_dir: Directory containing processed stock data
            model_dir: Directory to save trained models
        """
        self.data_dir = Path(data_dir)
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"TrendTrainer initialized: data_dir={self.data_dir}, "
            f"model_dir={self.model_dir}"
        )

    def load_data(self, symbols: list[str] | None = None) -> pl.DataFrame:
        """
        Load processed stock data from Sprint 1.

        Args:
            symbols: Optional list of stock symbols to filter

        Returns:
            DataFrame with stock data including OHLCV columns

        Raises:
            FileNotFoundError: If data file does not exist
        """
        from src.data_engine.storage import StorageInterface

        storage = StorageInterface()
        df = storage.load_stocks(symbols=symbols)

        if df.is_empty():
            logger.warning(f"No data loaded from {self.data_dir}")
        else:
            logger.info(f"Loaded {len(df)} rows for symbols: {symbols or 'all'}")

        return df

    def prepare_features(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Apply FeatureEngineer.transform() to add technical indicators.

        Args:
            df: DataFrame with OHLCV stock data

        Returns:
            DataFrame with added technical indicator columns

        Raises:
            ValueError: If DataFrame is empty
        """
        from src.ml_models.features import FeatureEngineer

        if df.is_empty():
            raise ValueError("Cannot prepare features on empty DataFrame")

        engineer = FeatureEngineer()
        df_features = engineer.transform(df)

        n_features = df_features.width - df.width
        logger.info(
            f"Prepared features: {n_features} new columns, "
            f"{df_features.height} samples"
        )

        return df_features

    def create_labels(self, df: pl.DataFrame) -> pl.Series:
        """
        Create up/down labels from close prices.

        Args:
            df: DataFrame with close price column

        Returns:
            Series with binary labels (0 or 1)
        """
        from src.ml_models.architecture.trend import TrendPredictor

        labels = TrendPredictor.create_labels(df.column("close"))

        n_up = labels.sum()
        up_rate = n_up / len(labels) if len(labels) > 0 else 0.0
        logger.info(f"Created labels: {n_up} up ({up_rate:.2%})")

        return labels

    def train(
        self,
        df: pl.DataFrame,
        labels: pl.Series,
        test_size: float = 0.2,
    ) -> dict:
        """
        Train XGBoost classifier with TimeSeriesSplit cross-validation.

        Args:
            df: DataFrame with feature columns
            labels: Series with binary labels
            test_size: Proportion of data for final test (not used in CV)

        Returns:
            dict with training metrics including:
                - accuracy, precision, recall, f1: Final training metrics
                - cv_f1_mean: Mean F1 score across CV folds
                - cv_f1_std: Standard deviation of F1 across folds
                - n_samples, n_features: Data dimensions
        """
        from src.ml_models.architecture.trend import TrendPredictor

        if df.is_empty():
            raise ValueError("Cannot train on empty DataFrame")
        if df.height != len(labels):
            raise ValueError(
                f"DataFrame height ({df.height}) != labels length ({len(labels)})"
            )

        predictor = TrendPredictor()

        # TimeSeriesSplit for time-appropriate cross-validation
        n_splits = 5
        tscv = TimeSeriesSplit(n_splits=n_splits)

        logger.info(f"Starting {n_splits}-fold TimeSeriesSplit cross-validation")

        cv_scores = []
        for fold, (train_idx, val_idx) in enumerate(tscv.split(df)):
            train_df = df.slice(train_idx[0], len(train_idx))
            val_df = df.slice(val_idx[0], len(val_idx))
            train_labels = labels.slice(train_idx[0], len(train_idx))
            val_labels = labels.slice(val_idx[0], len(val_idx))

            # Train on fold
            predictor.train(train_df, train_labels)

            # Evaluate on validation fold
            val_pred = predictor.predict(val_df).column("direction")
            val_labels_arr = val_labels.to_numpy()
            val_pred_arr = (val_pred.to_numpy() == "up").astype(int)

            fold_f1 = f1_score(val_labels_arr, val_pred_arr, zero_division=0)
            cv_scores.append(fold_f1)

            logger.debug(f"Fold {fold + 1}: F1 = {fold_f1:.3f}")

        # Calculate CV statistics
        cv_f1_mean = sum(cv_scores) / len(cv_scores)
        cv_f1_std = (
            sum((s - cv_f1_mean) ** 2 for s in cv_scores) / len(cv_scores)
        ) ** 0.5

        logger.info(
            f"Cross-validation complete: F1 = {cv_f1_mean:.3f} +/- {cv_f1_std:.3f}"
        )

        # Final training on all data
        logger.info("Training final model on all data")
        final_metrics = predictor.train(df, labels)
        final_metrics["cv_f1_mean"] = cv_f1_mean
        final_metrics["cv_f1_std"] = cv_f1_std

        # Save the model
        model_path = self.model_dir / "trend_predictor.joblib"
        predictor.save(model_path)
        logger.info(f"Model saved to {model_path}")

        return final_metrics

    def evaluate(
        self, predictor: TrendPredictor, df: pl.DataFrame, labels: pl.Series
    ) -> dict:
        """
        Compute classification metrics on test data.

        Args:
            predictor: Trained TrendPredictor
            df: DataFrame with features
            labels: Ground truth labels

        Returns:
            dict with classification metrics:
                - accuracy, precision, recall, f1
        """
        results = predictor.predict(df)
        pred_arr = (results.column("direction").to_numpy() == "up").astype(int)
        labels_arr = labels.to_numpy()

        metrics = {
            "accuracy": accuracy_score(labels_arr, pred_arr),
            "precision": precision_score(labels_arr, pred_arr, zero_division=0),
            "recall": recall_score(labels_arr, pred_arr, zero_division=0),
            "f1": f1_score(labels_arr, pred_arr, zero_division=0),
        }

        logger.info(
            f"Evaluation: accuracy={metrics['accuracy']:.3f}, "
            f"f1={metrics['f1']:.3f}"
        )

        return metrics


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "TrendTrainer",
]