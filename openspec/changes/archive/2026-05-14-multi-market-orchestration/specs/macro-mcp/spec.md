# Macro MCP

## Purpose
FRED MCP server exposing US macroeconomic indicators via MCP tools. Each indicator returns most recent observation value, date, and unit.

## Requirements

### Requirement: FRED MCP Integration
The system SHALL connect to FRED API via an MCP stdio transport server, exposing the following economic indicators through a unified `get_economic_indicator(series_id)` tool:

| # | Indicator | FRED Series ID |
|---|-----------|---------------|
| R1.1 | GDP | GDP |
| R1.2 | CPI / Inflation | CPIAUCSL |
| R1.3 | Unemployment Rate | UNRATE |
| R1.4 | Federal Funds Rate | FEDFUNDS |
| R1.5 | 10-Year Treasury Yield | DGS10 |
| R1.6 | 2-Year Treasury Yield | DGS2 |

Each SHALL return: `{value, date, units, series_id}`.

#### Scenario: Retrieve GDP data
- GIVEN MCP server running with valid FRED API key
- WHEN `get_economic_indicator("GDP")` is called
- THEN response SHALL include latest GDP value, observation date, and units (billions of dollars)

#### Scenario: Retrieve CPI and unemployment
- GIVEN MCP server connected
- WHEN `get_economic_indicator("CPIAUCSL")` is called
- THEN response SHALL include current CPI index value and date
- AND when `get_economic_indicator("UNRATE")` is called
- THEN response SHALL include current unemployment rate percentage

#### Scenario: Retrieve treasury yields
- GIVEN MCP server connected
- WHEN `get_economic_indicator("DGS10")` is called
- THEN response SHALL include 10-year Treasury yield as percentage

#### Scenario: FRED API unavailable
- GIVEN FRED API returns HTTP 503
- WHEN any macro tool is called
- THEN SHALL return "FRED API: service unavailable, try again later"
- AND MCP server SHALL remain running (graceful degradation)

#### Scenario: Invalid series ID
- GIVEN MCP server connected
- WHEN `get_economic_indicator("INVALID_SERIES")` is called
- THEN SHALL return "FRED API: series not found"
- AND SHALL NOT crash the MCP server
