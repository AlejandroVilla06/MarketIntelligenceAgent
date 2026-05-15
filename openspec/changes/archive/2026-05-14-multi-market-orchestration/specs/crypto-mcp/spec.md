# Crypto MCP

## Purpose
CoinMarketCap MCP server exposing cryptocurrency price, listing, and market data via MCP tools. API responses cached with 24h TTL to respect rate limits.

## Requirements

### Requirement: CoinMarketCap MCP Integration
The system SHALL connect to CoinMarketCap API via an MCP stdio transport server, exposing tools for crypto data retrieval with caching.

| Tool | Returns |
|------|---------|
| `get_crypto_price(symbol)` | price, market_cap, volume_24h, percent_change_24h |
| `get_crypto_listings(limit)` | top N cryptocurrencies by market cap |
| `get_global_metrics()` | total_market_cap, btc_dominance, total_volume_24h |

#### Scenario: Retrieve BTC price and market data
- GIVEN MCP server running with valid CoinMarketCap API key
- WHEN `get_crypto_price("BTC")` is called
- THEN response SHALL include price, market_cap, volume_24h, and percent_change_24h

#### Scenario: Retrieve top 10 by market cap
- GIVEN MCP server connected
- WHEN `get_crypto_listings(limit=10)` is called
- THEN response SHALL return 10 entries sorted by market_cap descending
- AND each entry SHALL include symbol, name, price, market_cap

#### Scenario: Cache hit avoids API call
- GIVEN BTC price was fetched 2 hours ago and cached
- WHEN `get_crypto_price("BTC")` is called again
- THEN cached response SHALL be returned without making an API call
- AND cache TTL SHALL be 24 hours

#### Scenario: Authentication failure
- GIVEN MCP server configured with invalid API key
- WHEN any crypto tool is called
- THEN SHALL return error "CoinMarketCap API: authentication failed"
- AND MCP server SHALL remain running (non-fatal error)

#### Scenario: Rate limit response
- GIVEN daily API call limit (333) has been exceeded
- WHEN any crypto tool is called
- THEN SHALL return "CoinMarketCap API: rate limit exceeded, retry after reset"
- AND cached data SHALL still be served if available
