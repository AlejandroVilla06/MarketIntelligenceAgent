# Delta for Market Query Agent

## ADDED Requirements

| ID | Requirement | Priority |
|----|------------|----------|
| REQ-MQA-005 | Silent context pipeline (two-stage) | Alta |
| REQ-MQA-006 | Cache validation | Alta |
| REQ-MQA-007 | Fallback safety (no data exposure) | Alta |
| REQ-MQA-008 | Multi-language data stripping | Alta |
| REQ-MQA-009 | DeepSeek provider configuration | Alta |

### Requirement: REQ-MQA-005 — Silent Context Pipeline

The agent SHALL use a two-stage pipeline: Stage 1 retrieves ChromaDB data invisibly, Stage 2 sends it as silent context to the LLM via `EXECUTIVE_ANALYSIS_PROMPT_TEMPLATE`. NEVER display raw data to the user.

#### Scenario: Two stages execute

- GIVEN a user query
- WHEN `run()` is called
- THEN Stage 1 SHALL retrieve without displaying data
- AND Stage 2 SHALL wrap data in `---BEGIN DATA---` / `---END DATA---`
- AND the user SHALL receive ONLY executive analysis

### Requirement: REQ-MQA-006 — Cache Validation

`_check_cache()` SHALL apply `_strip_data_sections()` and `_strip_react_artifacts()` to cached responses before returning them.

#### Scenario: Cache sanitizes dirty data

- GIVEN cache contains "Price Data: AAPL 170.2"
- WHEN `_check_cache()` returns this result
- THEN the stripping pipeline SHALL remove raw data headers
- AND the user SHALL NOT see data sections

#### Scenario: Cache hit with clean data passes through

- GIVEN cache contains only narrative executive analysis
- WHEN `_check_cache()` returns it
- THEN no stripping SHALL alter the content
- AND the response SHALL be returned as-is

### Requirement: REQ-MQA-007 — Fallback Safety

`_format_output()` SHALL NOT expose symbols, tickers, or raw ChromaDB data. SHALL return a generic error message instructing LLM credential setup.

#### Scenario: Fallback is safe

- GIVEN data contains symbols AAPL, MSFT and the LLM fails
- WHEN `_format_output()` is called
- THEN output SHALL NOT contain "AAPL", "MSFT", or any raw data

### Requirement: REQ-MQA-008 — Multi-Language Data Stripping

`_strip_data_sections()` SHALL detect and remove data headers in Spanish, English, French, German, Portuguese, and Italian, plus Markdown-formatted headers.

#### Scenario: Strips localized headers

- GIVEN output contains headers like "Datos de Precio:", "Données de Prix:", "Preisdaten:"
- WHEN `_strip_data_sections()` processes text
- THEN all localized headers SHALL be removed

#### Scenario: LLM leaks raw data despite prompt

- GIVEN the LLM outputs "Price Data: AAPL 170.2" or "Dados de Preço: PETR4 33.50"
- WHEN `_strip_data_sections()` runs as safety net
- THEN data-section lines SHALL be removed
- AND the remaining text SHALL be executive analysis only

### Requirement: REQ-MQA-009 — DeepSeek Provider

The agent SHALL support DeepSeek via `LLM_PROVIDER=deepseek` and `DEEPSEEK_API_KEY` in `.env`. When configured, it SHALL initialize `ChatOpenAI` with DeepSeek's base URL.

#### Scenario: DeepSeek configured

- GIVEN `LLM_PROVIDER=deepseek` and valid `DEEPSEEK_API_KEY`
- WHEN agent initializes the LLM
- THEN it SHALL use `api_base=https://api.deepseek.com/v1`

#### Scenario: DeepSeek key missing

- GIVEN `LLM_PROVIDER=deepseek` but `DEEPSEEK_API_KEY` is empty
- WHEN the agent attempts to call the LLM
- THEN it SHALL fall back to `_format_output()` with a safe error message
- AND the message SHALL NOT expose raw data

## MODIFIED Requirements

### Requirement: Agent Architecture (Previously: ReAct agent with tools)

The system SHALL use a two-stage pipeline: (1) keyword-based collection routing in `_retrieve_raw_data()`, (2) LLM executive analysis in `_generate_analysis()` using clean prompt. The system SHALL NOT use ReAct loop, LangChain tools, or `{agent_scratchpad}`.

#### Scenario: Pipeline routes by keyword

- GIVEN query "What is AAPL's price?"
- WHEN Stage 1 executes
- THEN it SHALL route to stocks collection (keyword "price")
- AND Stage 2 SHALL produce analysis in user's language

#### Scenario: Mixed query routes to all

- GIVEN query "How did earnings news affect NVDA price?"
- WHEN Stage 1 executes
- THEN it SHALL query all collections
- AND Stage 2 SHALL synthesize cross-domain analysis

### Requirement: Interface (Previously: exposed symbols in fallback, no cache validation)

The public interface SHALL remain `__init__()` and `run() -> str`. Internal contract changes:

- `_generate_analysis()`: SHALL use `build_analysis_prompt()` instead of `build_agent_prompt()` + regex-stripping
- `_check_cache()`: SHALL sanitize before return
- `_format_output()`: SHALL NOT expose symbols or data
- `_strip_react_artifacts()`: SHALL add language-specific patterns
- `_strip_data_sections()`: SHALL cover 6 languages + Markdown

#### Scenario: Error handling

- GIVEN the LLM fails mid-request
- WHEN `_generate_analysis()` catches the exception
- THEN it SHALL return `_format_output()` without symbols or data

## REMOVED Requirements

### Requirement: Reasoning Loop (ReAct)

(Reason: Replaced by silent-context pipeline. The agent no longer uses think-act-observe, ReAct prompt `{agent_scratchpad}`, or LangChain tool selection. This resolves the root cause of raw data leakage into user-facing output.)

## Non-Functional Requirements

| ID | Concern | Target |
|----|---------|--------|
| NFR-001 | Latency | No regression vs. current pipeline (no new LLM calls, same retriever) |
| NFR-002 | Cache compatibility | Existing semantic cache entries remain queryable; dirty entries sanitized on read |
| NFR-003 | Language coverage | es, en, fr, de, pt, it — stripping patterns cover all six |
| NFR-004 | Backward compat | `AGENT_SYSTEM_PROMPT_TEMPLATE` and `build_agent_prompt()` preserved; existing tests pass without modification |
