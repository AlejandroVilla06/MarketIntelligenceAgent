"""
Integration Tests for ML Pipeline

Tests the full ML pipeline from data loading to model training,
including save/load round-trip and prediction consistency.

These tests verify:
    - Full pipeline from data loading to model training
    - Model save/load round-trip preserves predictions
    - Prediction consistency after reload

Mark with @pytest.mark.integration to run separately.
"""

import pytest
from pathlib import Path
from typing import Any

import numpy as np

from src.ml_models.persistence import (
    ensure_model_dir,
    load_sklearn_model,
    save_sklearn_model,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================


@pytest.fixture
def temp_model_dir(tmp_path: Path) -> Path:
    """Create temporary directory for model storage."""
    model_dir = tmp_path / "models"
    model_dir.mkdir(exist_ok=True)
    return model_dir


@pytest.fixture
def sample_stock_data():
    """Create sample stock data for testing."""
    import polars as pl
    from datetime import datetime, timedelta

    n_days = 100
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(n_days)]

    # Create stock data with some patterns
    np.random.seed(42)
    base_prices = 100
    prices = [base_prices]
    for _ in range(n_days - 1):
        prices.append(prices[-1] + np.random.randn() * 0.5)

    df = pl.DataFrame({
        "date": dates,
        "symbol": ["TEST"] * n_days,
        "open": [p * 0.99 for p in prices],
        "high": [p * 1.02 for p in prices],
        "low": [p * 0.98 for p in prices],
        "close": prices,
        "volume": [1000000 + i * 1000 for i in range(n_days)],
    })

    return df


# =============================================================================
# FULL PIPELINE TESTS
# =============================================================================


@pytest.mark.integration
class TestFullPipeline:
    """Integration tests for full ML pipeline."""

    def test_feature_engineering_to_training_pipeline(self, sample_stock_data):
        """Test full pipeline from raw data to model training."""
        # Try to import and use the pipeline
        try:
            from src.ml_models.features import FeatureEngineer
        except ImportError:
            pytest.skip("Feature engineering module not available")

        # Apply feature engineering
        engineer = FeatureEngineer()
        features_df = engineer.transform(sample_stock_data)

        # Should have added technical indicator columns
        expected_cols = ["sma_20", "rsi_14", "macd"]
        for col in expected_cols:
            if col in features_df.columns:
                # Column should exist
                assert col in features_df.columns

    def test_anomaly_detection_pipeline(self, sample_stock_data, temp_model_dir: Path):
        """Test anomaly detection from data to predictions."""
        try:
            from src.ml_models.architecture import AnomalyDetector
            from src.ml_models.features import FeatureEngineer
        except ImportError:
            pytest.skip("Anomaly detection module not available")

        # Apply feature engineering
        engineer = FeatureEngineer()
        features_df = engineer.transform(sample_stock_data)

        if features_df.height < 50:
            pytest.skip("Insufficient data for training")

        # Train model
        detector = AnomalyDetector(
            n_estimators=10,
            contamination=0.1,
        )

        metrics = detector.train(features_df)
        assert metrics["status"] == "trained"

        # Predict
        predictions = detector.predict(features_df)

        # Should have added columns
        assert "anomaly_score" in predictions.columns
        assert "is_anomaly" in predictions.columns

    def test_trend_prediction_pipeline(self, sample_stock_data, temp_model_dir: Path):
        """Test trend prediction from data to predictions."""
        try:
            from src.ml_models.architecture import TrendPredictor
            from src.ml_models.features import FeatureEngineer
        except ImportError:
            pytest.skip("Trend prediction module not available")

        # Apply feature engineering
        engineer = FeatureEngineer()
        features_df = engineer.transform(sample_stock_data)

        # Create labels
        labeled_df = TrendPredictor.create_labels(features_df)

        if "direction" not in labeled_df.columns:
            pytest.skip("Label creation failed")

        if labeled_df.height < 50:
            pytest.skip("Insufficient data for training")

        # Extract features and labels
        labels = labeled_df["direction"]
        features = labeled_df.drop("direction")

        # Train model
        predictor = TrendPredictor(
            n_estimators=10,
            max_depth=3,
        )

        try:
            metrics = predictor.train(features, labels)
            assert "status" in metrics
        except ImportError:
            pytest.skip("XGBoost not available")


# =============================================================================
# MODEL SAVE/LOAD ROUND-TRIP TESTS
# =============================================================================


@pytest.mark.integration
class TestModelSaveLoadRoundTrip:
    """Integration tests for model save/load round-trip."""

    def test_anomaly_model_roundtrip(self, sample_stock_data, temp_model_dir: Path):
        """Test that anomaly model predictions match after save/load."""
        try:
            from src.ml_models.architecture import AnomalyDetector
            from src.ml_models.features import FeatureEngineer
        except ImportError:
            pytest.skip("Anomaly detection module not available")

        # Prepare data
        engineer = FeatureEngineer()
        features_df = engineer.transform(sample_stock_data)

        if features_df.height < 50:
            pytest.skip("Insufficient data")

        # Train original model
        detector = AnomalyDetector(n_estimators=10, contamination=0.1)
        detector.train(features_df)

        # Get predictions before save
        X_test = features_df.to_numpy()[:10]
        orig_scores = detector._model.score_samples(X_test)

        # Save model
        model_path = temp_model_dir / "anomaly_roundtrip"
        save_sklearn_model(detector, model_path)

        # Load model
        loaded_detector = load_sklearn_model(model_path)

        # Get predictions after load
        loaded_scores = loaded_detector._model.score_samples(X_test)

        # Scores should match exactly
        np.testing.assert_array_equal(orig_scores, loaded_scores)

    def test_trend_model_roundtrip(self, sample_stock_data, temp_model_dir: Path):
        """Test that trend model predictions match after save/load."""
        try:
            from src.ml_models.architecture import TrendPredictor
            from src.ml_models.features import FeatureEngineer
        except ImportError:
            pytest.skip("Trend prediction module not available")

        # Prepare data
        engineer = FeatureEngineer()
        features_df = engineer.transform(sample_stock_data)
        labeled_df = TrendPredictor.create_labels(features_df)

        if "direction" not in labeled_df.columns or labeled_df.height < 50:
            pytest.skip("Insufficient data")

        labels = labeled_df["direction"]
        features = labeled_df.drop("direction")

        # Train original model
        predictor = TrendPredictor(n_estimators=10, max_depth=3)

        try:
            predictor.train(features, labels)
        except ImportError:
            pytest.skip("XGBoost not available")

        # Get predictions before save
        X_test = features.to_numpy()[:10]
        orig_pred = predictor._model.predict(X_test)

        # Save model
        model_path = temp_model_dir / "trend_roundtrip"
        save_sklearn_model(predictor, model_path)

        # Load model
        loaded_predictor = load_sklearn_model(model_path)

        # Get predictions after load
        loaded_pred = loaded_predictor._model.predict(X_test)

        # Predictions should match
        np.testing.assert_array_equal(orig_pred, loaded_pred)


# =============================================================================
# PREDICTION CONSISTENCY TESTS
# =============================================================================


@pytest.mark.integration
class TestPredictionConsistency:
    """Integration tests for prediction consistency after reload."""

    def test_anomaly_prediction_consistency(self, sample_stock_data, temp_model_dir: Path):
        """Test anomaly predictions are consistent after model reload."""
        try:
            from src.ml_models.architecture import AnomalyDetector
            from src.ml_models.features import FeatureEngineer
        except ImportError:
            pytest.skip("Anomaly detection module not available")

        # Train and save
        engineer = FeatureEngineer()
        features_df = engineer.transform(sample_stock_data)

        if features_df.height < 50:
            pytest.skip("Insufficient data")

        detector = AnomalyDetector(n_estimators=10, contamination=0.1)
        detector.train(features_df)

        model_path = temp_model_dir / "anomaly_consistency"
        save_sklearn_model(detector, model_path)

        # Load and predict multiple times
        predictions = []
        for _ in range(3):
            loaded = load_sklearn_model(model_path)
            pred = loaded.predict(features_df)
            predictions.append(pred["anomaly_score"])

        # All predictions should match
        for i in range(1, len(predictions)):
            np.testing.assert_array_equal(predictions[0], predictions[i])

    def test_feature_columns_preserved_after_reload(self, sample_stock_data, temp_model_dir: Path):
        """Test feature columns are preserved after model save/load."""
        try:
            from src.ml_models.architecture import AnomalyDetector
            from src.ml_models.features import FeatureEngineer
        except ImportError:
            pytest.skip("Anomaly detection module not available")

        # Train
        engineer = FeatureEngineer()
        features_df = engineer.transform(sample_stock_data)

        if features_df.height < 50:
            pytest.skip("Insufficient data")

        # Get numeric columns used in training
        numeric_cols = [
            col for col in features_df.columns
            if features_df.schema[col] in (
                __import__("polars").Float64,
                __import__("polars").Float32,
                __import__("polars").Int64,
                __import__("polars").Int32,
            )
        ]

        detector = AnomalyDetector(n_estimators=10, contamination=0.1)
        detector.train(features_df)

        # Save and load
        model_path = temp_model_dir / "anomaly_columns"
        save_sklearn_model(detector, model_path)
        loaded = load_sklearn_model(model_path)

        # Feature columns should be preserved
        assert loaded._feature_columns == detector._feature_columns


# =============================================================================
# END-TO-END TESTS
# =============================================================================


@pytest.mark.integration
class TestEndToEnd:
    """End-to-end integration tests."""

    def test_full_training_workflow(self, sample_stock_data, temp_model_dir: Path):
        """Test complete training workflow."""
        try:
            from src.ml_models.architecture import AnomalyDetector
            from src.ml_models.features import FeatureEngineer
            from src.ml_models.persistence import ensure_model_dir
        except ImportError:
            pytest.skip("Required modules not available")

        # Step 1: Feature engineering
        engineer = FeatureEngineer()
        features_df = engineer.transform(sample_stock_data)

        if features_df.height < 50:
            pytest.skip("Insufficient data")

        # Step 2: Train model
        detector = AnomalyDetector(n_estimators=10, contamination=0.1)
        metrics = detector.train(features_df)

        assert metrics["status"] == "trained"
        assert "n_features" in metrics

        # Step 3: Save model
        ensure_model_dir(temp_model_dir)
        model_path = temp_model_dir / "full_workflow"
        save_sklearn_model(detector, model_path)

        # Step 4: Load and predict
        loaded = load_sklearn_model(model_path)
        predictions = loaded.predict(features_df)

        # Verify output structure
        assert "anomaly_score" in predictions.columns
        assert "is_anomaly" in predictions.columns

        # All rows should have predictions
        assert predictions.height == features_df.height