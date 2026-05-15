# Data Validation Specification

## Purpose

Define the requirements for validating and cleaning ingested data to ensure quality and consistency for downstream ML models and RAG agents.

## Requirements

### Requirement: Schema Validation

The system SHALL validate that ingested data conforms to the expected schema.

#### Scenario: Valid schema
- GIVEN a DataFrame with columns: ['date', 'open', 'high', 'low', 'close', 'volume', 'symbol']
- AND all columns have correct data types (date: datetime, open/high/low/close: float, volume: int, symbol: string)
- WHEN the data is validated
- THEN the system SHALL return the DataFrame unchanged
- AND the system SHALL log a validation success

#### Scenario: Missing required column
- GIVEN a DataFrame missing the 'volume' column
- WHEN the data is validated
- THEN the system SHALL raise a ValidationError
- AND the error message SHALL indicate the missing column

#### Scenario: Incorrect data type
- GIVEN a DataFrame where the 'close' column contains string values
- WHEN the data is validated
- THEN the system SHALL raise a ValidationError
- AND the error message SHALL indicate the column and expected type

### Requirement: Data Cleaning

The system SHALL clean common data quality issues in financial time series.

#### Scenario: Forward fill missing values
- GIVEN a DataFrame with occasional missing values in the 'close' column
- WHEN the data is cleaned
- THEN the system SHALL forward fill missing values (using previous valid value)
- AND the system SHALL log the number of values filled

#### Scenario: Remove duplicate rows
- GIVEN a DataFrame with duplicate rows (same date and symbol)
- WHEN the data is cleaned
- THEN the system SHALL remove duplicate rows, keeping the first occurrence
- AND the system SHALL log the number of duplicates removed

#### Scenario: Filter invalid prices
- GIVEN a DataFrame with negative or zero prices in 'open', 'high', 'low', 'close'
- WHEN the data is cleaned
- THEN the system SHALL remove rows with invalid prices
- AND the system SHALL log the number of rows removed

#### Scenario: Outlier detection using IQR
- GIVEN a DataFrame with extreme outliers in the 'volume' column
- WHEN the data is cleaned using IQR method
- THEN the system SHALL remove volume outliers (values below Q1-1.5*IQR or above Q3+1.5*IQR)
- AND the system SHALL log the number of outliers removed

### Requirement: Data Quality Reporting

The system SHALL generate a data quality report after validation and cleaning.

#### Scenario: Generate quality report
- GIVEN a DataFrame that has undergone validation and cleaning
- WHEN the quality report is generated
- THEN the system SHALL return a dictionary with metrics:
    - total_rows: initial row count
    - valid_rows: row count after validation
    - cleaned_rows: row count after cleaning
    - missing_values: count of missing values filled
    - duplicates_removed: count of duplicate rows removed
    - invalid_prices_removed: count of rows removed due to invalid prices
    - outliers_removed: count of outliers removed
- AND the system SHALL log the quality report

### Requirement: Configurable Validation Rules

The system SHALL allow configuration of validation rules via environment variables.

#### Scenario: Enable/disable validation steps
- GIVEN the environment variable VALIDATE_SCHEMA is set to "false"
- WHEN the data validation pipeline runs
- THEN the system SHALL skip schema validation
- AND the system SHALL log that schema validation was skipped

#### Scenario: Custom outlier threshold
- GIVEN the environment variable OUTLIER_IQR_MULTIPLIER is set to "2.0"
- WHEN the data is cleaned using IQR method
- THEN the system SHALL use 2.0 as the multiplier (instead of default 1.5)