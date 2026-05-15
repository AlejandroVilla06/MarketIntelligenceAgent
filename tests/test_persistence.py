"""
Tests for src.ml_models.persistence module.

Tests the model save/load round-trip functionality for both
sklearn and TensorFlow models, as well as directory creation.

Tests:
    - save_sklearn_model/load_sklearn_model round-trip
    - save_tensorflow_model/load_tensorflow_model round-trip
    - ensure_model_dir creates directory
"""

import pytest
import shutil
from pathlib import Path
from typing import Any

# Import joblib for comparison
import joblib

from src.ml_models.persistence import (
    ensure_model_dir,
    load_sklearn_model,
    load_tensorflow_model,
    save_sklearn_model,
    save_tensorflow_model,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================


@pytest.fixture
def temp_model_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for model storage."""
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    return model_dir


@pytest.fixture
def sklearn_model():
    """Create a simple sklearn model for testing."""
    from sklearn.ensemble import IsolationForest

    # Create and fit a simple model
    model = IsolationForest(
        n_estimators=10,
        contamination=0.1,
        random_state=42,
    )

    # Fit on simple data
    import numpy as np
    X = np.random.RandomState(42).randn(100, 4)
    model.fit(X)

    return model


@pytest.fixture
def xgboost_model():
    """Create a simple XGBoost model for testing."""
    try:
        from xgboost import XGBClassifier

        # Create and fit a simple model
        model = XGBClassifier(
            n_estimators=10,
            max_depth=3,
            learning_rate=0.1,
            random_state=42,
            verbosity=0,
        )

        # Fit on simple data
        import numpy as np
        X = np.random.RandomState(42).randn(100, 4)
        y = (X[:, 0] > 0).astype(int)
        model.fit(X, y)

        return model
    except ImportError:
        pytest.skip("XGBoost not installed")


# =============================================================================
# TEST ENSURE_MODEL_DIR
# =============================================================================


class TestEnsureModelDir:
    """Test cases for ensure_model_dir function."""

    def test_ensure_model_dir_creates_directory(self, tmp_path: Path):
        """Test that ensure_model_dir creates directory if it doesn't exist."""
        model_dir = tmp_path / "new_model_dir"

        # Directory should not exist yet
        assert not model_dir.exists()

        # Call ensure_model_dir
        result = ensure_model_dir(model_dir)

        # Directory should now exist
        assert model_dir.exists()
        assert model_dir.is_dir()
        assert result == model_dir

    def test_ensure_model_dir_existing_directory(self, tmp_path: Path):
        """Test that ensure_model_dir handles existing directory."""
        model_dir = tmp_path / "existing_dir"
        model_dir.mkdir()

        # Call ensure_model_dir on existing directory
        result = ensure_model_dir(model_dir)

        # Should return the same path
        assert result == model_dir
        assert model_dir.exists()

    def test_ensure_model_dir_nested_path(self, tmp_path: Path):
        """Test that ensure_model_dir creates nested directories."""
        nested_path = tmp_path / "nested" / "deep" / "path"

        # Call ensure_model_dir
        result = ensure_model_dir(nested_path)

        # All directories should be created
        assert nested_path.exists()
        assert nested_path.is_dir()
        assert result == nested_path

    def test_ensure_model_dir_returns_path_object(self, tmp_path: Path):
        """Test that ensure_model_dir returns a Path object."""
        model_dir = tmp_path / "model_dir"

        result = ensure_model_dir(model_dir)

        # Should return Path object
        assert isinstance(result, Path)
        assert result == model_dir


# =============================================================================
# TEST SKLEARN MODEL SAVE/LOAD
# =============================================================================


class TestSklearnModelPersistence:
    """Test cases for sklearn model save/load."""

    def test_save_sklearn_model_creates_file(self, temp_model_dir: Path, sklearn_model: Any):
        """Test that save_sklearn_model creates a .joblib file."""
        filepath = temp_model_dir / "detector"

        # Save model
        save_sklearn_model(sklearn_model, filepath)

        # File should exist
        assert filepath.with_suffix(".joblib").exists()

    def test_load_sklearn_model(self, temp_model_dir: Path, sklearn_model: Any):
        """Test loading sklearn model."""
        filepath = temp_model_dir / "detector"

        # Save and load
        save_sklearn_model(sklearn_model, filepath)
        loaded_model = load_sklearn_model(filepath)

        # Model should be loaded
        assert loaded_model is not None
        assert hasattr(loaded_model, "predict")

    def test_save_load_roundtrip_preserves_model(self, temp_model_dir: Path, sklearn_model: Any):
        """Test that save/load round-trip preserves model functionality."""
        import numpy as np

        filepath = temp_model_dir / "detector"

        # Save and load
        save_sklearn_model(sklearn_model, filepath)
        loaded_model = load_sklearn_model(filepath)

        # Generate test data
        X_test = np.random.RandomState(123).randn(10, 4)

        # Both models should produce same predictions
        orig_predictions = sklearn_model.predict(X_test)
        loaded_predictions = loaded_model.predict(X_test)

        assert np.array_equal(orig_predictions, loaded_predictions)

    def test_save_sklearn_model_with_extension(self, temp_model_dir: Path, sklearn_model: Any):
        """Test saving with explicit .joblib extension."""
        filepath = temp_model_dir / "detector.joblib"

        # Save model
        save_sklearn_model(sklearn_model, filepath)

        # Should exist
        assert filepath.exists()

    def test_load_sklearn_nonexistent_file(self, temp_model_dir: Path):
        """Test loading non-existent model raises error."""
        filepath = temp_model_dir / "nonexistent"

        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            load_sklearn_model(filepath)

    def test_save_sklearn_model_none_raises_error(self, temp_model_dir: Path):
        """Test saving None model raises error."""
        filepath = temp_model_dir / "detector"

        # Should raise ValueError
        with pytest.raises(ValueError):
            save_sklearn_model(None, filepath)


# =============================================================================
# TEST XGBOOST MODEL SAVE/LOAD
# =============================================================================


class TestXGBoostModelPersistence:
    """Test cases for XGBoost model save/load."""

    def test_xgboost_save_load_roundtrip(self, temp_model_dir: Path, xgboost_model: Any):
        """Test that XGBoost save/load round-trip preserves model."""
        import numpy as np

        filepath = temp_model_dir / "predictor"

        # Save and load
        save_sklearn_model(xgboost_model, filepath)
        loaded_model = load_sklearn_model(filepath)

        # Generate test data
        X_test = np.random.RandomState(123).randn(10, 4)

        # Both models should produce same predictions
        orig_predictions = xgboost_model.predict(X_test)
        loaded_predictions = loaded_model.predict(X_test)

        assert np.array_equal(orig_predictions, loaded_predictions)


# =============================================================================
# TEST TENSORFLOW MODEL SAVE/LOAD
# =============================================================================


class TestTensorFlowModelPersistence:
    """Test cases for TensorFlow model save/load."""

    @pytest.fixture(autouse=True)
    def check_tf_available(self):
        """Skip tests if TensorFlow is not available."""
        try:
            import tensorflow as tf
        except ImportError:
            pytest.skip("TensorFlow not installed")

    def test_save_tensorflow_model_creates_directory(self, temp_model_dir: Path):
        """Test that save_tensorflow_model creates SavedModel directory."""
        try:
            from tensorflow import keras
            from tensorflow.keras import layers
        except ImportError:
            pytest.skip("TensorFlow not installed")

        # Create a simple model
        inputs = keras.Input(shape=(4,))
        outputs = layers.Dense(1)(inputs)
        model = keras.Model(inputs=inputs, outputs=outputs)

        filepath = temp_model_dir / "lstm_model"

        # Save model
        save_tensorflow_model(model, filepath)

        # Directory should exist (SavedModel format)
        assert filepath.exists()
        assert filepath.is_dir()

    def test_load_tensorflow_model(self, temp_model_dir: Path):
        """Test loading TensorFlow model."""
        try:
            from tensorflow import keras
            from tensorflow.keras import layers
        except ImportError:
            pytest.skip("TensorFlow not installed")

        # Create a simple model
        inputs = keras.Input(shape=(4,))
        outputs = layers.Dense(1)(inputs)
        model = keras.Model(inputs=inputs, outputs=outputs)

        filepath = temp_model_dir / "lstm_model"

        # Save and load
        save_tensorflow_model(model, filepath)
        loaded_model = load_tensorflow_model(filepath)

        # Model should be loaded
        assert loaded_model is not None
        assert hasattr(loaded_model, "predict")

    def test_tensorflow_save_load_roundtrip(self, temp_model_dir: Path):
        """Test that TensorFlow save/load preserves model functionality."""
        try:
            import numpy as np
            from tensorflow import keras
            from tensorflow.keras import layers
        except ImportError:
            pytest.skip("TensorFlow not installed")

        # Create and train a simple model
        inputs = keras.Input(shape=(4,))
        outputs = layers.Dense(1)(inputs)
        model = keras.Model(inputs=inputs, outputs=outputs)

        model.compile(optimizer="adam", loss="mse")

        # Train on simple data
        X_train = np.random.RandomState(42).randn(100, 4)
        y_train = np.random.RandomState(42).randn(100, 1)
        model.fit(X_train, y_train, epochs=1, verbose=0)

        filepath = temp_model_dir / "lstm_model"

        # Save and load
        save_tensorflow_model(model, filepath)
        loaded_model = load_tensorflow_model(filepath)

        # Generate test data
        X_test = np.random.RandomState(123).randn(10, 4)

        # Both models should produce similar predictions
        orig_predictions = model.predict(X_test, verbose=0)
        loaded_predictions = loaded_model.predict(X_test, verbose=0)

        # Predictions should be very close
        assert np.allclose(orig_predictions, loaded_predictions, rtol=1e-5)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


@pytest.mark.integration
class TestPersistenceIntegration:
    """Integration tests for model persistence."""

    def test_anomaly_detector_save_load(self, temp_model_dir: Path):
        """Test AnomalyDetector save/load round-trip."""
        from sklearn.ensemble import IsolationForest
        import numpy as np

        # Create and fit model
        model = IsolationForest(n_estimators=10, random_state=42)
        X = np.random.RandomState(42).randn(100, 4)
        model.fit(X)

        filepath = temp_model_dir / "anomaly_detector"

        # Save and load
        save_sklearn_model(model, filepath)
        loaded_model = load_sklearn_model(filepath)

        # Test predictions match
        X_test = np.random.RandomState(123).randn(10, 4)
        orig_scores = model.score_samples(X_test)
        loaded_scores = loaded_model.score_samples(X_test)

        assert np.allclose(orig_scores, loaded_scores)


@pytest.mark.integration
class TestMultiModelPersistence:
    """Test persisting multiple models to same directory."""

    def test_multiple_models_same_dir(self, temp_model_dir: Path):
        """Test saving multiple models to same directory."""
        from sklearn.ensemble import (
            IsolationForest,
            RandomForestClassifier,
        )
        import numpy as np

        # Create training data
        X = np.random.RandomState(42).randn(100, 4)
        y = (X[:, 0] > 0).astype(int)

        # Train and save anomaly detector
        anomaly_model = IsolationForest(n_estimators=10, random_state=42)
        anomaly_model.fit(X)
        save_sklearn_model(anomaly_model, temp_model_dir / "anomaly")

        # Train and save classifier
        classifier = RandomForestClassifier(n_estimators=10, random_state=42)
        classifier.fit(X, y)
        save_sklearn_model(classifier, temp_model_dir / "classifier")

        # Both files should exist
        assert (temp_model_dir / "anomaly.joblib").exists()
        assert (temp_model_dir / "classifier.joblib").exists()

        # Load both
        loaded_anomaly = load_sklearn_model(temp_model_dir / "anomaly")
        loaded_classifier = load_sklearn_model(temp_model_dir / "classifier")

        # Both should work
        assert loaded_anomaly is not None
        assert loaded_classifier is not None