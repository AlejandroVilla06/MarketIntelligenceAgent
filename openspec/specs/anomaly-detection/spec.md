# Anomaly Detection Specification

## Purpose

Define the requirements for detecting anomalies in stock market data using Isolation Forest and Autoencoder models. The system shall identify unusual price or volume patterns that deviate from normal behavior.

## Requirements

### Requirement: Model Selection and Configuration

The system SHALL support multiple anomaly detection algorithms configurable via environment variables.

#### Scenario: Isolation Forest configuration
- GIVEN the environment variable ANOMALY_MODEL is set to "isolation_forest"
- WHEN the anomaly detector is initialized
- THEN the system SHALL use Isolation Forest with configurable parameters:
    - n_estimators: from ANOMALY_N_ESTIMATORS (default: 100)
    - contamination: from ANOMALY_CONTAMINATION (default: 0.1)
    - max_samples: from ANOMALY_MAX_SAMPLES (default: "auto")

#### Scenario: Autoencoder configuration
- GIVEN the environment variable ANOMALY_MODEL is set to "autoencoder"
- WHEN the anomaly detector is initialized
- THEN the system SHALL use a neural network Autoencoder with configurable parameters:
    - encoding_dim: from ANOMALY_ENCODING_DIM (default: 16)
    - layers: from ANOMALY_LAYERS (default: "64,32,16,32,64")
    - epochs: from ANOMALY_EPOCHS (default: 100)

### Requirement: Training with Normal Data

The system SHALL train on normal (non-anomalous) stock data to establish baseline behavior.

#### Scenario: Training with clean data
- GIVEN a DataFrame with stock data that contains only normal patterns
- WHEN the anomaly detector is trained
- THEN the system SHALL fit the model on the training data
- AND the system SHALL log training progress and final metrics

#### Scenario: Training data validation
- GIVEN a DataFrame with missing values or invalid prices
- WHEN training is attempted
- THEN the system SHALL raise a DataValidationError
- AND the error message SHALL indicate the validation failure

### Requirement: Anomaly Detection

The system SHALL detect anomalies based on reconstruction error or anomaly score threshold.

#### Scenario: Detect anomalies in test data
- GIVEN a trained anomaly detector and a DataFrame with mixed normal and anomalous data
- WHEN the detector is run on the test data
- THEN the system SHALL return a DataFrame with added columns:
    - anomaly_score: float representing anomaly score (higher = more anomalous)
    - is_anomaly: boolean indicating if the row is an anomaly (True/False)
- AND the system SHALL log the number of anomalies detected

#### Scenario: Configurable threshold
- GIVEN the environment variable ANOMALY_THRESHOLD is set to 0.7
- WHEN the detector is run
- THEN a data point SHALL be flagged as anomaly if its score exceeds 0.7

### Requirement: Model Persistence

The system SHALL save trained models and load them for inference.

#### Scenario: Save trained model
- GIVEN a trained anomaly detector
- WHEN the save() method is called with a filepath
- THEN the system SHALL save the model to disk in a format compatible with scikit-learn/tensorflow
- AND the system SHALL log the save location

#### Scenario: Load trained model
- GIVEN a saved model file exists at the specified path
- WHEN the load() method is called with the filepath
- THEN the system SHALL load the model into memory
- AND the system SHALL return a ready-to-use detector

### Requirement: Evaluation Metrics

The system SHALL compute and log evaluation metrics after training.

#### Scenario: Training metrics
- GIVEN a trained model
- WHEN training is complete
- THEN the system SHALL compute and log:
    - training_time: seconds to train
    - n_samples_train: number of training samples
    - model_type: Isolation Forest or Autoencoder
    - feature_names: list of input features

#### Scenario: Anomaly statistics
- GIVEN a DataFrame with anomaly detection results
- WHEN statistics are requested
- THEN the system SHALL return:
    - total_samples: number of data points analyzed
    - anomalies_detected: count of anomalies
    - anomaly_rate: percentage of anomalies
    - average_score: mean anomaly score