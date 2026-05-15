"""
Model Persistence Module
========================

Save and load trained ML models to/from disk using joblib and TensorFlow.

This module provides functions for serializing sklearn models
and TensorFlow/Keras models, with automatic directory creation
and error handling.

Functions:
    save_sklearn_model: Save sklearn model using joblib
    load_sklearn_model: Load sklearn model from joblib file
    save_tensorflow_model: Save TensorFlow/Keras model
    load_tensorflow_model: Load TensorFlow/Keras model
    ensure_model_dir: Create model directory if needed

Usage:
    from src.ml_models.persistence import (
        save_sklearn_model,
        load_sklearn_model,
        ensure_model_dir,
    )

    # Ensure directory exists
    model_dir = ensure_model_dir("models/anomaly")

    # Save sklearn model
    save_sklearn_model(model, "models/anomaly/detector")

    # Load sklearn model
    model = load_sklearn_model("models/anomaly/detector")
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import joblib

from src.utils import get_logger

# Import TensorFlow conditionally to avoid hard dependency
if TYPE_CHECKING:
    import tensorflow as tf
else:
    try:
        import tensorflow as tf
        TF_AVAILABLE = True
    except ImportError:
        TF_AVAILABLE = False


# =============================================================================
# LOGGING
# =============================================================================

logger = get_logger(__name__)


# =============================================================================
# DIRECTORY UTILITIES
# =============================================================================


def ensure_model_dir(model_dir: str | Path) -> Path:
    """
    Create model directory if it doesn't exist.

    Creates all parent directories as needed and returns
    the normalized Path object.

    Args:
        model_dir: Directory path to ensure exists

    Returns:
        The Path object for the directory

    Examples:
        >>> path = ensure_model_dir("models/anomaly")
        >>> path
        PosixPath('models/anomaly')

        >>> path = ensure_model_dir("data/models/v1")
        >>> path.exists()
        True
    """
    path = Path(model_dir)

    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created model directory: {path}")

    return path


# =============================================================================
# SKLEARN MODEL PERSISTENCE
# =============================================================================


def save_sklearn_model(model: Any, filepath: str | Path) -> None:
    """
    Save sklearn-compatible model using joblib.

    Saves the model to a .joblib file. Use this function for
    scikit-learn models, XGBoost, and any model supporting
    joblib serialization.

    Args:
        model: sklearn-compatible model to save
        filepath: Path to save the model (with or without .joblib extension)

    Raises:
        OSError: If file cannot be written
        ValueError: If model is None

    Examples:
        >>> from sklearn.ensemble import IsolationForest
        >>> model = IsolationForest()
        >>> model.fit(X_train)
        >>> save_sklearn_model(model, "models/anomaly/detector")
    """
    if model is None:
        raise ValueError("Cannot save None model")

    filepath = Path(filepath)

    # Add .joblib extension if not present
    if filepath.suffix != ".joblib":
        filepath = filepath.with_suffix(".joblib")

    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Save model using joblib
    joblib.dump(model, filepath)

    logger.info(f"Saved sklearn model to {filepath}")


def load_sklearn_model(filepath: str | Path) -> Any:
    """
    Load sklearn-compatible model from joblib file.

    Loads a model previously saved with save_sklearn_model().

    Args:
        filepath: Path to the saved model file (.joblib extension)

    Returns:
        The loaded model object

    Raises:
        FileNotFoundError: If model file does not exist
        OSError: If file cannot be read

    Examples:
        >>> model = load_sklearn_model("models/anomaly/detector")
        >>> predictions = model.predict(X_test)
    """
    filepath = Path(filepath)

    # Add .joblib extension if not present
    if filepath.suffix != ".joblib":
        filepath = filepath.with_suffix(".joblib")

    if not filepath.exists():
        raise FileNotFoundError(f"Model file not found: {filepath}")

    # Load model using joblib
    model = joblib.load(filepath)

    logger.info(f"Loaded sklearn model from {filepath}")

    return model


# =============================================================================
# TENSORFLOW MODEL PERSISTENCE
# =============================================================================


def save_tensorflow_model(model: Any, filepath: str | Path) -> None:
    """
    Save TensorFlow/Keras model usingSavedModel format.

    Saves the model in TensorFlow's SavedModel format, which
    preserves the full model architecture, weights, and configuration.

    Note: Requires TensorFlow to be installed.

    Args:
        model: TensorFlow/Keras model to save
        filepath: Path to save the model (directory for SavedModel,
                 or .h5/.keras for HDF5 format)

    Raises:
        ImportError: If TensorFlow is not installed
        ValueError: If model is None
        OSError: If file cannot be written

    Examples:
        >>> model = build_lstm_model()
        >>> model.fit(X_train, y_train)
        >>> save_tensorflow_model(model, "models/lstm/forecaster")
    """
    if not TF_AVAILABLE:
        raise ImportError(
            "TensorFlow is not installed. "
            "Install with: pip install tensorflow"
        )

    if model is None:
        raise ValueError("Cannot save None model")

    # Import keras for saving
    try:
        from tensorflow import keras
    except ImportError:
        raise ImportError("TensorFlow/Keras is not available")

    filepath = Path(filepath)

    # Determine save format based on extension
    if filepath.suffix in (".h5", ".keras"):
        # Save as HDF5/Keras format
        filepath.parent.mkdir(parents=True, exist_ok=True)
        model.save(filepath)
        logger.info(f"Saved TensorFlow model to {filepath}")
    else:
        # Save as SavedModel format (directory)
        filepath.mkdir(parents=True, exist_ok=True)
        # Use save_format='tf' for SavedModel format
        model.save(str(filepath), save_format="tf")
        logger.info(f"Saved TensorFlow model to {filepath}/")


def load_tensorflow_model(filepath: str | Path) -> Any:
    """
    Load TensorFlow/Keras model.

    Loads a model previously saved with save_tensorflow_model()
    or saved via model.save().

    Note: Requires TensorFlow to be installed.

    Args:
        filepath: Path to the saved model (directory or .h5/.keras file)

    Returns:
        Loaded Keras model

    Raises:
        ImportError: If TensorFlow is not installed
        FileNotFoundError: If model does not exist
        OSError: If file cannot be read

    Examples:
        >>> model = load_tensorflow_model("models/lstm/forecaster")
        >>> predictions = model.predict(X_test)
    """
    if not TF_AVAILABLE:
        raise ImportError(
            "TensorFlow is not installed. "
            "Install with: pip install tensorflow"
        )

    # Import keras for loading
    try:
        from tensorflow import keras
    except ImportError:
        raise ImportError("TensorFlow/Keras is not available")

    filepath = Path(filepath)

    # Determine load method based on path
    if filepath.is_file():
        # Load from HDF5/Keras file
        if not filepath.exists():
            raise FileNotFoundError(f"Model file not found: {filepath}")
        model = keras.models.load_model(filepath)
        logger.info(f"Loaded TensorFlow model from {filepath}")
    else:
        # Load from SavedModel directory
        if not filepath.exists():
            raise FileNotFoundError(f"Model directory not found: {filepath}")
        model = keras.models.load_model(str(filepath))
        logger.info(f"Loaded TensorFlow model from {filepath}/")

    return model


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "save_sklearn_model",
    "load_sklearn_model",
    "save_tensorflow_model",
    "load_tensorflow_model",
    "ensure_model_dir",
]