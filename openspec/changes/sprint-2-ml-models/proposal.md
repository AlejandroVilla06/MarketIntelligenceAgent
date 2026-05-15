# Proposal: Sprint 2 - ML Models Layer

## Intent

Build the machine learning layer for anomaly detection and trend prediction in stock market data. This layer consumes processed data from the data ingestion layer (Sprint 1) and provides predictive insights to the RAG agents.

## Scope

### In Scope
- Anomaly detection model using Isolation Forest or Autoencoder
- Trend prediction model using XGBoost for price direction
- LSTM model for time-series forecasting (stretch goal)
- Model training pipeline with hyperparameter tuning
- Model evaluation and metrics (precision, recall, F1, RMSE, etc.)
- Model persistence (save/load to disk)
- Feature engineering for ML (technical indicators)

### Out of Scope
- Real-time model inference (streaming)
- Model deployment as microservice
- Automated retraining pipelines
- Deep learning sentiment analysis (use TextBlob/VADER from Sprint 1)

## Capabilities (New)
- `anomaly-detection`: Detect anomalies in stock price/volume data
- `trend-prediction`: Predict price direction (up/down) using XGBoost
- `lstm-forecasting`: Time-series forecasting with LSTM (stretch goal)
- `feature-engineering`: Calculate technical indicators (RSI, MACD, Bollinger Bands)
- `model-persistence`: Save/load trained models to disk

## Approach

1. **Feature Engineering**: Create technical indicators from OHLCV data (RSI, MACD, Bollinger Bands, SMA, EMA)
2. **Anomaly Detection**: Train Isolation Forest on normal patterns, flag anomalies when reconstruction error exceeds threshold
3. **Trend Prediction**: Train XGBoost classifier on price direction (binary: up/down)
4. **LSTM Forecasting**: Build and train LSTM for multi-step price forecasting (if time permits)
5. **Evaluation**: Use time-series cross-validation and holdout sets

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/ml_models/architecture/` | New | Model definitions (IsolationForest, XGBoost, LSTM) |
| `src/ml_models/trainers/` | New | Training scripts with hyperparameter tuning |
| `src/ml_models/features/` | New | Feature engineering utilities (technical indicators) |
| `src/ml_models/persistence/` | New | Model save/load utilities |
| `data/processed/` | Input | Stock data from Sprint 1 |
| `tests/` | New | Unit tests for ML components |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| LSTM training slow without GPU | Medium | Use CPU-optimized TF, limit epochs, offer GPU config option |
| Overfitting on small datasets | Medium | Use cross-validation, limit model complexity, regularization |
| Model selection for time-series | Low | Use time-series specific splits, avoid random train/test split |
| Feature engineering errors | Low | Unit tests for each indicator, validate against known values |

## Rollback Plan

1. Remove newly created directories: `src/ml_models/architecture/`, `src/ml_models/trainers/`, `src/ml_models/features/`, `src/ml_models/persistence/`
2. Revert any changes to existing files (none expected)
3. Sprint 1 data layer remains unaffected
4. No breaking changes to existing code

## Dependencies

- Python packages: scikit-learn, xgboost, tensorflow (or pytorch), pandas, polars
- Data: Processed stock data from Sprint 1 (data/processed/)
- Config: Model hyperparameters from environment variables

## Success Criteria

- [ ] Isolation Forest detects known anomalies in test data
- [ ] XGBoost achieves >60% accuracy on price direction prediction
- [ ] Models can be saved and loaded correctly
- [ ] Tests cover model training and evaluation (>80% coverage)
- [ ] Feature engineering produces meaningful technical indicators
- [ ] Documentation explains model usage and limitations