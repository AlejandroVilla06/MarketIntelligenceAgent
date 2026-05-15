# Delta for News Sentiment Ingestion

## MODIFIED Requirements

### Requirement: Sentiment Analysis

The system SHALL perform sentiment analysis on news articles using NLP models. The system SHALL support multiple sentiment providers: TextBlob, VADER, and Llama 3.1 via Ollama.
(Previously: Only TextBlob and VADER were supported)

#### Scenario: TextBlob sentiment
- GIVEN an English news article with positive language about a stock
- WHEN sentiment analysis is performed
- THEN the system SHALL return a polarity score between -1 and 1
- AND positive text SHALL yield a score > 0
- AND negative text SHALL yield a score < 0
- AND neutral text SHALL yield a score near 0

#### Scenario: VADER sentiment for social media text
- GIVEN a financial tweet or Reddit post
- WHEN VADER sentiment analysis is performed
- THEN the system SHALL return a compound score between -1 and 1
- AND the system SHALL handle financial slang and emojis appropriately

#### Scenario: Llama 3.1 sentiment analysis
- GIVEN a financial news article
- WHEN Llama 3.1 sentiment analysis is selected as the provider
- THEN the system SHALL connect to Ollama for inference
- AND the system SHALL return a score between -1 and 1
- AND the system SHALL consider financial context in the assessment

#### Scenario: Llama fallback
- GIVEN Llama 3.1 is configured but Ollama is not available
- WHEN the news pipeline runs
- THEN the system SHALL automatically fall back to the configured fallback provider (TextBlob or VADER)
- AND the pipeline SHALL continue without error