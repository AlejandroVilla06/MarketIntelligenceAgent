# Design: Sprint 2 - ML Models Layer

## Technical Approach

Build the ML layer using scikit-learn for traditional ML (Isolation Forest, XGBoost) and TensorFlow/Keras for deep learning (LSTM, Autoencoder). All models consume processed stock data from Sprint 1 and produce predictions for consumption by RAG agents.

## Architecture Decisions

### Decision: sklearn over PyTorch for traditional ML

**Choice**: Use scikit-learn for Isolation Forest and XGBoost, TensorFlow for LSTM/Autoencoder.

**Alternatives considered**: PyTorch for all models, just scikit-learn, just XGBoost for everything.

**Rationale**: sklearn provides excellent implementations for Isolation Forest and is well-tested. XGBoost has sklearn-compatible API. TensorFlow integrates well for sequential models (LSTM) and autoencoders. Mixing frameworks is acceptable when each is used for its strengths.

### Decision: Feature Engineering as a separate module

**Choice**: Create `src/ml_models/features/` module for all technical indicator calculations.

**Alternatives considered**: Include feature engineering in each model class, compute features in data pipeline (Sprint 1).

**Rationale**: Separation of concerns - feature engineering is independent of which model uses the features. Reusability - same features can be used by anomaly detection, trend prediction, and LSTM. Testability - features can be unit tested in isolation.

### Decision: Model persistence with joblib

**Choice**: Use joblib for sklearn models, TensorFlow's save_format for deep learning.

**Alternatives considered**: Pickle for everything, ONNX for cross-framework serialization.

**Rationale**: joblib is sklearn's recommended serialization format and handles large numpy arrays efficiently. TensorFlow's save_format is native and ensures compatibility when loading. Both are well-supported and stable.

### Decision: Time-series cross-validation

**Choice**: Use sklearn TimeSeriesSplit for validation to avoid look-ahead bias.

**Alternatives considered**: Random train/test split, k-fold cross-validation.

**Rationale**: Time-series data has temporal dependencies - random splits would leak future information into training. TimeSeriesSplit respects temporal order and simulates real deployment.

## Data Flow

```
data/processed/ (Sprint 1)
       │
       ▼
┌──────────────────┐
│ Feature          │
│ Engineering      │  ← Technical indicators
│ (features/)      │    SMA, EMA, RSI, MACD, BB
└──────────────────┘
       │
       ├──────────────────┬──────────────────┐
       ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Anomaly      │  │ Trend        │  │ LSTM         │
│ Detection    │  │ Prediction   │  │ Forecasting  │
│ (Isolation   │  │ (XGBoost)    │  │ (TensorFlow) │
│ Forest)      │  │              │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
       │                  │                  │
       ▼                  ▼                  ▼
  anomaly_score      direction          forecast
  is_anomaly         confidence        next_prices
       │                  │                  │
       └──────────────────┼──────────────────┘
                          ▼
                  ┌──────────────┐
                  │ RAG Agent    │
                  │ (Sprint 3)  │
                  └──────────────┘
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/ml_models/features/__init__.py` | Create | Export feature engineering functions |
| `src/ml_models/features/indicators.py` | Create | Technical indicator calculations |
| `src/ml_models/features/transformer.py` | Create | DataFrame transformation with all indicators |
| `src/ml_models/architecture/__init__.py` | Create | Export model classes |
| `src/ml_models/architecture/anomaly.py` | Create | AnomalyDetector class (Isolation Forest, Autoencoder) |
| `src/ml_models/architecture/trend.py` | Create | TrendPredictor class (XGBoost) |
| `src/ml_models/architecture/lstm.py` | Create | LSTMForecaster class (stretch goal) |
| `src/ml_models/trainers/__init__.py` | Create | Export trainer classes |
| `src/ml_models/trainers/anomaly_trainer.py` | Create | Training logic for anomaly detection |
| `src/ml_models/trainers/trend_trainer.py` | Create | Training logic for trend prediction |
| `src/ml_models/persistence/__init__.py` | Create | Export model save/load functions |
| `src/ml_models/persistence/model_io.py` | Create | Save and load functions |
| `tests/test_features.py` | Create | Unit tests for feature engineering |
| `tests/test_anomaly.py` | Create | Unit tests for anomaly detection |
| `tests/test_trend.py` | Create | Unit tests for trend prediction |

## Interfaces / Contracts

### FeatureEngineering Module
```python
class FeatureEngineer:
    """Computes technical indicators from OHLCV data."""
    def __init__(self, sma_period: int = 20, rsi_period: int = 14, ...):
        ...
    def calculate_sma(self, df: pl.DataFrame, column: str = "close") -> pl.Series:
        """Simple Moving Average."""
        ...
    def calculate_ema(self, df: pl.DataFrame, column: str = "close") -> pl.Series:
        """Exponential Moving Average."""
        ...
    def calculate_rsi(self, df: pl.DataFrame, column: str = "close") -> pl.Series:
        """Relative Strength Index."""
        ...
    def calculate_macd(self, df: pl.DataFrame) -> dict[str, pl.Series]:
        """MACD (line, signal, histogram)."""
        ...
    def calculate_bollinger_bands(self, df: pl.DataFrame) -> dict[str, pl.Series]:
        """Bollinger Bands (upper, middle, lower)."""
        ...
    def transform(self, df: pl.DataFrame) -> pl.DataFrame:
        """Add all indicators as columns to DataFrame."""
        ...
```

### AnomalyDetector Interface
```python
class AnomalyDetector:
    """Detects anomalies in stock data."""
    def __init__(self, model_type: str = "isolation_forest", **config):
        ...
    def train(self, df: pl.DataFrame) -> TrainingMetrics:
        """Train on normal data."""
        ...
    def predict(self, df: pl.DataFrame) -> pl.DataFrame:
        """Predict anomalies. Returns DataFrame with anomaly_score, is_anomaly columns."""
        ...
    def save(self, filepath: str) -> None:
        """Save model to disk."""
        ...
    @classmethod
    def load(cls, filepath: str) -> AnomalyDetector:
        """Load model from disk."""
        ...
```

### TrendPredictor Interface
```python
class TrendPredictor:
    """Predicts price direction (up/down)."""
    def __init__(self, n_estimators: int = 100, max_depth: int = 6, **config):
        ...
    def train(self, df: pl.DataFrame, labels: pl.Series) -> TrainingMetrics:
        """Train on features and labels."""
        ...
    def predict(self, df: pl.DataFrame) -> PredictionResult:
        """Predict direction with confidence."""
        ...
    def get_feature_importance(self) -> list[tuple[str, float]]:
        """Return sorted feature importance."""
        ...
    def save(self, filepath: str) -> None:
        """Save model to disk."""
        ...
    @classmethod
    def load(cls, filepath: str) -> TrendPredictor:
        """Load model from disk."""
        ...
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Feature engineering calculations | Known input/output pairs for each indicator |
| Unit | AnomalyDetector training | Mock training data, check model.fit called |
| Unit | TrendPredictor training | Mock features and labels, check accuracy |
| Unit | Model save/load | Round-trip save and load, verify predictions match |
| Integration | Full pipeline | Train on historical data, predict on test set, verify metrics |
| Property | Feature computation | Use hypothesis to generate random DataFrames and verify invariants |

## Migration / Rollback

**No migration required.** This is a new feature addition.

- New directories created: `src/ml_models/features/`, `src/ml_models/architecture/`, `src/ml_models/trainers/`, `src/ml_models/persistence/`
- No changes to existing Sprint 1 code
- No changes to data formats or storage

To rollback:
1. Remove `src/ml_models/` directory entirely
2. Remove `tests/test_features.py`, `tests/test_anomaly.py`, `tests/test_trend.py`
3. Sprint 1 remains fully functional

## Open Questions

- [ ] Should LSTM be a hard requirement or remain stretch goal?
- [ ] What minimum accuracy threshold should trigger retraining?
- [ ] Should we implement model versioning (keep last N versions)?
- [ ] Should we add early stopping for LSTM training?
- [ ] Should we support GPU acceleration for training (CUDA config)?