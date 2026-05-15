# Llama Sentiment Analyzer Specification

## Purpose

Define requirements for analyzing financial news sentiment using Llama 3.1 via Ollama with LangChain. This provides higher quality sentiment analysis compared to rule-based models (TextBlob, VADER).

## Requirements

### Requirement: Ollama Connection

The system SHALL connect to a local Ollama instance for LLM inference.

#### Scenario: Valid Ollama connection
- GIVEN Ollama is running locally on the configured host
- WHEN the sentiment analyzer initializes
- THEN the system SHALL establish a connection to the Ollama API
- AND the system SHALL be ready to analyze sentiment

#### Scenario: Ollama not available
- GIVEN Ollama is not running or not accessible
- WHEN the sentiment analyzer initializes
- THEN the system SHALL raise a connection error
- AND the fallback analyzer SHALL be used instead

### Requirement: Llama Sentiment Analysis

The system SHALL analyze financial news text using Llama 3.1 and return a sentiment score.

#### Scenario: Analyze positive financial news
- GIVEN a news article with positive language ("stocks surge", "record profits", "bullish outlook")
- WHEN the Llama analyzer processes the text
- THEN the system SHALL return a score between 0.5 and 1.0
- AND the response SHALL indicate positive sentiment

#### Scenario: Analyze negative financial news
- GIVEN a news article with negative language ("stocks plunge", "losses mount", "bearish trend")
- WHEN the Llama analyzer processes the text
- THEN the system SHALL return a score between -1.0 and -0.5
- AND the response SHALL indicate negative sentiment

#### Scenario: Analyze neutral financial news
- GIVEN a news article with neutral language ("company reports earnings", "quarterly results announced")
- WHEN the Llama analyzer processes the text
- THEN the system SHALL return a score between -0.3 and 0.3
- AND the response SHALL indicate neutral sentiment

### Requirement: Financial Domain Prompt

The system SHALL use a specialized prompt for financial sentiment analysis.

#### Scenario: Financial context understanding
- GIVEN a news article mentioning "bear market", "bull run", "dividend yield", "P/E ratio"
- WHEN the Llama analyzer processes the text
- THEN the system SHALL consider financial context in its sentiment assessment
- AND the score SHALL reflect understanding of financial terminology

### Requirement: Fallback to Traditional Analyzers

The system SHALL fall back to TextBlob or VADER when Ollama is unavailable.

#### Scenario: Fallback activation
- GIVEN the Llama analyzer fails to connect or times out
- WHEN the system attempts sentiment analysis
- THEN the system SHALL automatically use the configured fallback analyzer
- AND the user SHALL not notice any difference in the pipeline output

### Requirement: Configuration via Environment

The system SHALL allow configuration of Ollama connection through environment variables.

#### Scenario: Custom Ollama host
- GIVEN the environment variable OLLAMA_HOST is set to "http://localhost:11434"
- WHEN the sentiment analyzer initializes
- THEN the system SHALL connect to the specified host

#### Scenario: Custom model selection
- GIVEN the environment variable OLLAMA_MODEL is set to "llama3:8b"
- WHEN the sentiment analyzer runs
- THEN the system SHALL use the specified model for inference