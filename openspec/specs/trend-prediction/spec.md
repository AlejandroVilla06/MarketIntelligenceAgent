# Trend Prediction Specification

## Purpose

Define the requirements for predicting stock price direction (up/down) using XGBoost classifier. The system shall analyze historical price patterns and technical indicators to forecast whether the price will increase or decrease.

## Requirements

### Requirement: Binary Classification Output

The system SHALL predict price direction as a binary classification (up/down).

#### Scenario: Predict price up
- GIVEN a trained XGBoost model and current market data for symbol AAPL
- WHEN the predictor is run
- THEN the system SHALL return a prediction of "up" or "down"
- AND the system SHALL provide a confidence score between 0 and 1

#### Scenario: Output format
- GIVEN a prediction request
- WHEN the system predicts
- THEN the output SHALL contain:
    - direction: "up" or "down"
    - confidence: float between 0 and 1
    - probability_up: float between 0 and 1
    - probability_down: float between 0 and 1

### Requirement: XGBoost Model Configuration

The system SHALL support configurable XGBoost hyperparameters via environment variables.

#### Scenario: Default configuration
- GIVEN no environment variables are set
- WHEN the model is initialized
- THEN the system SHALL use sensible defaults:
    - n_estimators: 100
    - max_depth: 6
    - learning_rate: 0.1
    - objective: binary:logistic

#### Scenario: Custom hyperparameters
- GIVEN the environment variable XGBOOST_N_ESTIMATORS is set to 200
- AND XGBOOST_MAX_DEPTH is set to 8
- WHEN the model is initialized
- THEN the system SHALL use n_estimators=200 and max_depth=8

### Requirement: Training with Labeled Data

The system SHALL train on historical data with known price directions.

#### Scenario: Create training labels
- GIVEN a DataFrame with historical stock prices (close prices over time)
- WHEN labels are created
- THEN the system SHALL calculate daily price change
- AND label "up" if close_t > close_t-1, else "down"
- AND store labels as integer (1 for up, 0 for down)

#### Scenario: Train XGBoost classifier
- GIVEN features (technical indicators) and labels (price direction)
- WHEN the trainer is run
- THEN the system SHALL fit XGBoost with the training data
- AND the system SHALL log training progress, accuracy, and feature importances

### Requirement: Feature Importance

The system SHALL report which features most influence predictions.

#### Scenario: Get top features
- GIVEN a trained XGBoost model
- WHEN feature importance is requested
- THEN the system SHALL return a sorted list of (feature_name, importance_score) pairs
- AND the system SHALL log the top 5 most important features

### Requirement: Model Persistence

The system SHALL save trained models and load them for inference.

#### Scenario: Save trained model
- GIVEN a trained XGBoost model
- WHEN save() is called with a filepath
- THEN the system SHALL save the model using joblib
- AND the system SHALL log the save location

#### Scenario: Load trained model
- GIVEN a saved model file exists
- WHEN load() is called with the filepath
- THEN the system SHALL load the model into memory
- AND the system SHALL return a ready-to-use predictor

### Requirement: Evaluation Metrics

The system SHALL compute classification metrics during training and evaluation.

#### Scenario: Training metrics
- GIVEN training data with labels
- WHEN training completes
- THEN the system SHALL compute and log:
    - accuracy: overall classification accuracy
    - precision: precision for "up" class
    - recall: recall for "up" class
    - f1_score: F1 score for "up" class

#### Scenario: Cross-validation
- GIVEN training data
- WHEN cross-validation is requested
- THEN the system SHALL use TimeSeriesSplit with n_splits=5
- AND report mean accuracy and standard deviation