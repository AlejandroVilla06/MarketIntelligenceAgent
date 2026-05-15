# Tasks: Sprint 2 - ML Models Layer

## Phase 1: Feature Engineering Module

- [x] 1.1 Create `src/ml_models/features/__init__.py` to export feature engineering functions
- [x] 1.2 Create `src/ml_models/features/indicators.py`:
    - Add calculate_sma() function (Simple Moving Average)
    - Add calculate_ema() function (Exponential Moving Average)
    - Add calculate_rsi() function (Relative Strength Index)
    - Add calculate_macd() function (MACD line, signal, histogram)
    - Add calculate_bollinger_bands() function (upper, middle, lower)
    - Add calculate_volume_features() function (volume_sma, volume_ratio)
- [x] 1.3 Create `src/ml_models/features/transformer.py`:
    - Add FeatureEngineer class to coordinate all indicators
    - Add transform() method to add all indicators as columns to DataFrame
    - Add configurable period parameters via __init__
- [x] 1.4 Create `tests/test_features.py` with unit tests for all indicator functions

## Phase 2: Model Architecture

- [x] 2.1 Create `src/ml_models/architecture/__init__.py` to export model classes
- [x] 2.2 Create `src/ml_models/architecture/anomaly.py`:
    - Add AnomalyDetector class with Isolation Forest implementation
    - Add train() method accepting normal data DataFrame
    - Add predict() method returning DataFrame with anomaly_score and is_anomaly columns
    - Add save() and load() class methods for model persistence
    - Add configurable hyperparameters via __init__
- [x] 2.3 Create `src/ml_models/architecture/trend.py`:
    - Add TrendPredictor class with XGBoost classifier
    - Add train() method accepting features DataFrame and labels Series
    - Add predict() method returning PredictionResult (direction, confidence, probabilities)
    - Add get_feature_importance() method returning sorted list of (name, importance) pairs
    - Add save() and load() class methods
    - Add create_labels() static method to convert price data to up/down labels
- [x] 2.4 Create `src/ml_models/architecture/lstm.py`:
    - Add LSTMForecaster class (stretch goal)
    - Add build_model() method to construct LSTM architecture
    - Add train() method with early stopping support
    - Add predict() method for multi-step forecasting
    - Add save() and load() methods using TensorFlow format
- [x] 2.5 Create `tests/test_anomaly.py` and `tests/test_trend.py` with unit tests

## Phase 3: Model Training

- [x] 3.1 Create `src/ml_models/trainers/__init__.py` to export trainer classes
- [x] 3.2 Create `src/ml_models/trainers/anomaly_trainer.py`:
    - Add AnomalyTrainer class to orchestrate training workflow
    - Add load_data() method to read processed stock data from Sprint 1
    - Add prepare_training_data() method to filter normal patterns
    - Add train() method to train and return metrics
    - Add evaluate() method to compute anomaly statistics
- [x] 3.3 Create `src/ml_models/trainers/trend_trainer.py`:
    - Add TrendTrainer class to orchestrate training workflow
    - Add load_data() method to read processed stock data
    - Add prepare_features() method to apply FeatureEngineer.transform()
    - Add create_labels() method to generate up/down labels from price data
    - Add train() method with cross-validation
    - Add evaluate() method to compute classification metrics
- [x] 3.4 Create `tests/test_trainers.py` with integration-style tests

## Phase 4: Model Persistence

- [x] 4.1 Create `src/ml_models/persistence/__init__.py` to export save/load functions
- [x] 4.2 Create `src/ml_models/persistence/model_io.py`:
    - Add save_sklearn_model() function using joblib
    - Add load_sklearn_model() function
    - Add save_tensorflow_model() function using TF save_format
    - Add load_tensorflow_model() function
    - Add ensure_model_dir() function to create model directories
- [x] 4.3 Create `tests/test_persistence.py` with round-trip save/load tests

## Phase 5: Integration and CLI

- [x] 5.1 Create `run_ml_training.py` CLI script:
    - Add argparse for command-line options (--anomaly, --trend, --lstm, --all)
    - Add model configuration via environment variables
    - Add logging with progress reporting
    - Add error handling with exit codes
- [x] 5.2 Create `tests/test_ml_integration.py`:
    - Test full pipeline from data loading to model training
    - Test model save/load round-trip
    - Test prediction consistency after reload
- [x] 5.3 Update `README.md` with ML usage examples and configuration

## Phase 6: Documentation

- [x] 6.1 Add docstrings to all new classes and functions following existing style
- [x] 6.2 Create `docs/ml-models.md` with:
    - Architecture diagram
    - Usage examples for each model type
    - Configuration options table
    - Model limitations and best practices
- [x] 6.3 Verify all imports work correctly via smoke tests
- [x] 6.4 Run pytest to verify all tests pass