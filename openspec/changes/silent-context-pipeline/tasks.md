# Tasks: Silent Context Pipeline

## Phase 1: Foundation (Prompt & Config)

- [ ] 1.1 Create `EXECUTIVE_ANALYSIS_PROMPT_TEMPLATE` in `src/agents/chains/prompts.py` after L228
  - Inherit persona, language protocol, executive structure, sector frameworks, security constraint from `AGENT_SYSTEM_PROMPT_TEMPLATE` (L22-98)
  - Remove: `{input}`, `{agent_scratchpad}`, tools list, `Begin!`, `Question:`, `# 🛠 AVAILABLE TOOLS`
  - Add placeholders: `{language}`, `{chat_history}`, `{user_profile}`, `{data_context}`
  - Add explicit Silent Context instruction prohibiting reproduction of raw data
  - Must be plain `str`, NOT `PromptTemplate`

- [ ] 1.2 Create `build_analysis_prompt(language, chat_history, user_profile, data_context)` in `src/agents/chains/prompts.py`
  - Returns `str` (NOT `PromptTemplate`)
  - Uses `.format()` or `.replace()` to fill placeholders
  - Validate all 6 languages produce correct output

- [ ] 1.3 Update `.env` with DeepSeek configuration
  - Add `# DeepSeek Configuration` section
  - Add `LLM_PROVIDER=deepseek`, `DEEPSEEK_API_KEY=tu_key`, `DEEPSEEK_API_BASE=https://api.deepseek.com/v1`
  - Include descriptive comments for each variable

## Phase 2: Core Implementation (Agent Logic)

- [ ] 2.1 Refactor `_generate_analysis()` in `src/agents/query_agent.py` (L550-636)
  - Replace `build_agent_prompt()` call with `build_analysis_prompt()`
  - Pass: `language`, `chat_history`, `user_profile`, `data_context`
  - Delete lines 580-591 (regex stripping block for ReAct artifacts)
  - Simplify `user_message`: keep query + `---BEGIN DATA---\n{data}\n---END DATA---` only
  - `system` message = output of `build_analysis_prompt()`

- [ ] 2.2 Expand `_strip_data_sections()` in `src/agents/query_agent.py` (L700-739)
  - Add patterns: Markdown tables `\|.*\|.*\|`, bullets with bold `^\s*-\s*\*\*.*\*\*.*$`
  - Add multi-language headers: Price (es/en/fr/de/pt/it), News (es/en/fr/de/pt/it), Sentiment (es/en/de/pt/it)
  - Add numeric lines: `^\s*[\d\.,]+\s*[%$€£¥]?\s*$`, `^\s*[A-Z]{1,5}\s+[\d\.,]+\s*$`
  - Add quality check: if >3 lines match data patterns, log warning and set `has_data_leak=True`

- [ ] 2.3 Rewrite `_format_output()` in `src/agents/query_agent.py` (L741-774)
  - Ignore `data` parameter completely
  - Return constant: `"No fue posible generar el análisis ejecutivo en este momento. Verifica que el LLM esté correctamente configurado."`
  - Must NOT reveal symbols, tickers, or raw data

## Phase 3: Integration (Safety Nets)

- [ ] 3.1 Sanitize `_check_cache()` in `src/agents/query_agent.py` (L464-479)
  - Before returning, pass `cached_result` through `_strip_data_sections()` and `_strip_react_artifacts()`
  - If sanitized result is empty or len < 50 chars, return `None`
  - Log invalidation events

## Phase 4: Testing

- [ ] 4.1 Update `tests/test_query_agent.py` (L33-86)
  - `test_format_output_list` and `test_format_output_dict`: expect generic error message, NOT symbols
  - Update `test_format_output_empty_list` and `test_format_output_string` if they assert old behavior
  - Leave ReAct artifact tests untouched

- [ ] 4.2 Add tests for `build_analysis_prompt()` in `tests/test_prompts.py`
  - Test renders for 6 languages
  - Test NO ReAct artifacts in output
  - Test silent context instruction is present
  - Existing `test_prompt_has_tool_instructions` must remain unchanged

- [ ] 4.3 Run full test suite `pytest tests/ -v`
  - All existing tests pass (backward compat)
  - New tests pass
  - No regressions in query agent tests
