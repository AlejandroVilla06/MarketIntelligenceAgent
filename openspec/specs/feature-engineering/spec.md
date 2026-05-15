# Feature Engineering Specification

## Purpose

Define the requirements for computing technical indicators from OHLCV stock data. These indicators serve as features for the anomaly detection and trend prediction models.

## Requirements

### Requirement: Technical Indicators

The system SHALL compute common technical indicators for stock analysis.

#### Scenario: Simple Moving Average (SMA)
- GIVEN a DataFrame with 'close' prices and a period parameter (default: 20)
- WHEN SMA is calculated
- THEN the system SHALL return a Series with the moving average
- AND the output SHALL be added as 'sma_{period}' column to the DataFrame

#### Scenario: Exponential Moving Average (EMA)
- GIVEN a DataFrame with 'close' prices and a period parameter (default: 12)
- WHEN EMA is calculated
- THEN the system SHALL return the exponential moving average
- AND the output SHALL be added as 'ema_{period}' column

#### Scenario: Relative Strength Index (RSI)
- GIVEN a DataFrame with 'close' prices and a period parameter (default: 14)
- WHEN RSI is calculated
- THEN the system SHALL return values between 0 and 100
- AND the output SHALL be added as 'rsi_{period}' column
- AND values above 70 SHALL indicate overbought conditions
- AND values below 30 SHALL indicate oversold conditions

#### Scenario: MACD (Moving Average Convergence Divergence)
- GIVEN a DataFrame with 'close' prices
- WHEN MACD is calculated with default parameters (fast=12, slow=26, signal=9)
- THEN the system SHALL compute:
    - macd_line: EMA(fast) - EMA(slow)
    - signal_line: EMA(macd_line, signal period)
    - histogram: macd_line - signal_line
- AND add columns: 'macd', 'macd_signal', 'macd_histogram'

#### Scenario: Bollinger Bands
- GIVEN a DataFrame with 'close' prices and a period parameter (default: 20)
- WHEN Bollinger Bands are calculated
- THEN the system SHALL compute:
    - middle_band: SMA(period)
    - upper_band: SMA + (2 * std)
    - lower_band: SMA - (2 * std)
- AND add columns: 'bb_upper', 'bb_middle', 'bb_lower'

#### Scenario: Volume-based features
- GIVEN a DataFrame with 'volume' and 'close' prices
- WHEN volume features are calculated
- THEN the system SHALL compute:
    - volume_sma: SMA of volume over period (default: 20)
    - volume_ratio: current volume / volume_sma
- AND add columns: 'volume_sma', 'volume_ratio'

### Requirement: DataFrame Transformation

The system SHALL add all computed indicators as new columns to the input DataFrame.

#### Scenario: Transform full DataFrame
- GIVEN a DataFrame with columns: date, open, high, low, close, volume, symbol
- WHEN transform() is called
- THEN the system SHALL add all computed technical indicators as new columns
- AND the original columns SHALL remain unchanged
- AND new columns SHALL include: sma_20, ema_12, rsi_14, macd, macd_signal, macd_histogram, bb_upper, bb_middle, bb_lower, volume_sma, volume_ratio

#### Scenario: Preserve DataFrame metadata
- GIVEN a DataFrame with existing columns and metadata
- WHEN transformation is applied
- THEN the system SHALL preserve the original columns
- AND add new indicator columns without modifying existing data
- AND handle missing values gracefully (forward fill or NaN)

### Requirement: Configurable Periods

The system SHALL allow configuration of indicator periods via environment variables.

#### Scenario: Custom SMA period
- GIVEN the environment variable SMA_PERIOD is set to 30
- WHEN SMA is calculated
- THEN the system SHALL use period=30 instead of default 20

#### Scenario: Custom RSI period
- GIVEN the environment variable RSI_PERIOD is set to 21
- WHEN RSI is calculated
- THEN the system SHALL use period=21 instead of default 14

### Requirement: Input Validation

The system SHALL validate that required columns exist before computing indicators.

#### Scenario: Missing required column
- GIVEN a DataFrame missing the 'close' column
- WHEN any indicator is calculated
- THEN the system SHALL raise a ValueError
- AND the error message SHALL indicate "Missing required column: close"

#### Scenario: Invalid price data
- GIVEN a DataFrame with negative or zero prices
- WHEN indicator calculation is attempted
- THEN the system SHALL log a warning
- AND proceed with calculation (indicators may produce NaN for invalid data)