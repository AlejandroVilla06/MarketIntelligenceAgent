# Hierarchical Orchestrator

## Purpose
Multi-market routing architecture with intent classification, domain delegation, and fall-back synthesis. Existing stocks pipeline SHALL remain untouched.

## Requirements

### Requirement: Hierarchical Architecture
The system SHALL route all queries through RouterAgent to domain sub-orchestrators (stocks, crypto, macro, calculation). Stocks pipeline SHALL pass through with zero behavior change.

#### Scenario: Stocks query delegated unchanged
- GIVEN user query "What's AAPL price?"
- WHEN RouterAgent classifies as stocks (confidence >= 0.7)
- THEN query SHALL delegate to StocksSubOrchestrator
- AND existing MarketQueryAgent SHALL process it unchanged

#### Scenario: Crypto query delegated
- GIVEN user query "What's BTC price?"
- WHEN RouterAgent classifies as crypto (confidence >= 0.7)
- THEN query SHALL delegate to CryptoSubOrchestrator

#### Scenario: Macro query delegated
- GIVEN user query "Current GDP growth rate"
- WHEN RouterAgent classifies as macro (confidence >= 0.7)
- THEN query SHALL delegate to MacroSubOrchestrator

### Requirement: RouterAgent Classification
The RouterAgent SHALL classify queries via keyword matching, providing a confidence score (0.0-1.0). Confidence >= 0.7 SHALL route directly; < 0.7 SHALL trigger fall-back.

#### Scenario: High-confidence direct route
- GIVEN query "Bitcoin price in USD today"
- WHEN RouterAgent matches crypto keywords at confidence 0.95
- THEN query SHALL route directly to CryptoSubOrchestrator
- AND no other sub-orchestrators SHALL be queried

#### Scenario: Low-confidence triggers fall-back
- GIVEN query "how does inflation affect cryptocurrency"
- WHEN RouterAgent confidence is 0.45 (straddles macro + crypto domains)
- THEN fall-back mode SHALL activate

### Requirement: Fall-back Mechanism
When confidence < 0.7, the RouterAgent SHALL query ALL sub-orchestrators in parallel, collect results, and synthesize via a single LLM call. SHALL NOT return empty when data exists in any domain.

#### Scenario: Multi-domain query synthesized via fall-back
- GIVEN query "GDP growth effect on BTC price" classified at confidence 0.4
- WHEN fall-back queries stocks, crypto, macro sub-orchestrators in parallel
- AND macro and crypto return valid data
- THEN LLM synthesis SHALL produce unified response referencing both GDP and BTC data

#### Scenario: Fall-back with partial results
- GIVEN fall-back mode queries all sub-orchestrators
- WHEN only crypto returns data (stocks and macro empty)
- THEN synthesis SHALL report available crypto data
- AND SHALL note that macro and stocks data was unavailable

#### Scenario: RouterAgent is single entry point
- GIVEN any user query
- WHEN `MarketOrchestrator.ask(query)` is called
- THEN RouterAgent SHALL be the first component invoked
- AND no sub-orchestrator SHALL be invoked directly by the orchestrator
