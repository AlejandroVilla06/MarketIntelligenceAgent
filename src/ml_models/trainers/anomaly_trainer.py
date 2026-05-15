"""
Anomaly Detection Trainer
==========================

Orchestrates training workflow for anomaly detection models.

Usage:
    from src.ml_models.trainers import AnomalyTrainer

    trainer = AnomalyTrainer()
    df = trainer.load_data(symbols=["AAPL"])
    df_normal = trainer.prepare_training_data(df, exclude_anomalies=True)
    detector = trainer.train(df_normal, feature_columns)
    results = trainer.evaluate(detector, df)
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from src.utils import get_logger


# =============================================================================
# LOGGING
# =============================================================================

logger = get_logger(__name__)


# =============================================================================
# ANOMALY TRAINER
# =============================================================================


class AnomalyTrainer:
    """
    Handles loading data, preparing training data,
    training, and evaluation for anomaly detection.

    Responsibilities:
    - Load processed stock data
    - Prepare training data (normal patterns only)
    - Train anomaly detector
    - Evaluate and report anomalies

    Usage:
        trainer = AnomalyTrainer()
        df = trainer.load_data(symbols=["AAPL"])
        df_normal = trainer.prepare_training_data(df, exclude_anomalies=True)
        detector = trainer.train(df_normal, feature_columns)
        results = trainer.evaluate(detector, df)
    """

    def __init__(
        self,
        data_dir: str | Path = "data/processed/stocks",
        model_dir: str | Path = "src/ml_models/saved",
    ) -> None:
        """
        Initialize AnomalyTrainer with directories.

        Args:
            data_dir: Directory containing processed stock data
            model_dir: Directory to save trained models
        """
        self.data_dir = Path(data_dir)
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"AnomalyTrainer initialized: data_dir={self.data_dir}, "
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

    def prepare_training_data(
        self,
        df: pl.DataFrame,
        exclude_anomalies: bool = True,
    ) -> pl.DataFrame:
        """
        Filter and prepare training data (normal patterns only).

        For now, returns all data. In a production system, this would
        filter out known anomalies based on historical labels or
        statistical thresholds.

        Args:
            df: DataFrame with stock data
            exclude_anomalies: Whether to exclude known anomalies

        Returns:
            DataFrame with normal patterns only
        """
        # For now, return all data - filtering for anomalies is model-dependent
        # In production, would filter based on labeled anomalies or statistical filters
        logger.info(
            f"Prepared training data: {len(df)} samples "
            f"(exclude_anomalies={exclude_anomalies})"
        )
        return df

    def train(
        self,
        df: pl.DataFrame,
        feature_columns: list[str],
    ) -> object:
        """
        Train anomaly detector on prepared data.

        Args:
            df: DataFrame with feature columns
            feature_columns: List of column names to use as features

        Returns:
            Trained AnomalyDetector instance

        Raises:
            ValueError: If DataFrame is empty or feature columns invalid
        """
        from src.ml_models.architecture.anomaly import AnomalyDetector

        if df.is_empty():
            raise ValueError("Cannot train on empty DataFrame")

        # Select only the specified feature columns
        available_cols = [col for col in feature_columns if col in df.columns]
        missing_cols = set(feature_columns) - set(available_cols)

        if missing_cols:
            logger.warning(f"Missing columns: {missing_cols}")

        df_features = df.select(available_cols)

        logger.info(
            f"Training AnomalyDetector on {len(df_features)} samples "
            f"with {len(available_cols)} features"
        )

        detector = AnomalyDetector()
        metrics = detector.train(df_features)

        logger.info(
            f"Training complete: {metrics['n_samples']} samples, "
            f"{metrics['n_features']} features"
        )

        # Save the model
        model_path = self.model_dir / "anomaly_detector.joblib"
        detector.save(model_path)
        logger.info(f"Model saved to {model_path}")

        return detector

    def evaluate(self, detector: object, df: pl.DataFrame) -> dict:
        """
        Compute and return anomaly statistics.

        Args:
            detector: Trained AnomalyDetector
            df: DataFrame to evaluate

        Returns:
            dict with anomaly statistics:
                - total_samples: Number of samples evaluated
                - anomalies_detected: Number of anomalies found
                - anomaly_rate: Proportion of anomalies
        """
        if df.is_empty():
            raise ValueError("Cannot evaluate on empty DataFrame")

        results = detector.predict(df)
        n_anomalies = results.column("is_anomaly").sum()
        anomaly_rate = float(n_anomalies / len(df)) if len(df) > 0 else 0.0

        metrics = {
            "total_samples": len(df),
            "anomalies_detected": int(n_anomalies),
            "anomaly_rate": anomaly_rate,
        }

        logger.info(
            f"Evaluation: {metrics['anomalies_detected']} anomalies "
            f"({anomaly_rate:.2%} anomaly rate)"
        )

        return metrics


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "AnomalyTrainer",
]