# Silent Context Prompt Specification

## Purpose

Define the `EXECUTIVE_ANALYSIS_PROMPT_TEMPLATE` and `build_analysis_prompt()` for the two-stage pipeline (retrieve → analyze). The prompt MUST NOT contain ReAct artifacts, and MUST instruct the LLM that ChromaDB data is silent context never to be reproduced.

## Requirements

| ID | Requirement | Priority |
|----|------------|----------|
| REQ-SCP-001 | Clean template without ReAct | Alta |
| REQ-SCP-002 | Silent context instructions | Alta |
| REQ-SCP-003 | Multi-language support (es,en,fr,de,pt,it) | Alta |
| REQ-SCP-004 | Executive analysis structure mandate | Media |

### Requirement: REQ-SCP-001 — Clean Prompt Template

The template `EXECUTIVE_ANALYSIS_PROMPT_TEMPLATE` SHALL contain NO `{input}`, `{agent_scratchpad}`, `Begin!`, `Question:`, `# 🛠 AVAILABLE TOOLS`, or tool descriptions.

#### Scenario: No ReAct artifacts

- GIVEN the template is loaded
- WHEN inspected for ReAct tokens
- THEN none of `{input}`, `{agent_scratchpad}`, `Begin!`, or tool lists SHALL be found

### Requirement: REQ-SCP-002 — Silent Context

The prompt SHALL instruct the LLM that `---BEGIN DATA---` / `---END DATA---` blocks are invisible context for analysis only. The instructions SHALL prohibit reproducing raw sections (Price Data, News, Sentiment) in any language.

#### Scenario: Data treated as invisible

- GIVEN data is wrapped in `---BEGIN DATA---` / `---END DATA---` markers
- WHEN the LLM generates a response
- THEN the output SHALL NOT contain those markers or raw data section headers

### Requirement: REQ-SCP-003 — Multi-Language

`build_analysis_prompt(language)` SHALL accept all 6 supported languages and produce a filled template with language-specific instructions.

#### Scenario: Language parameter renders

- GIVEN language="pt"
- WHEN `build_analysis_prompt("pt")` is called
- THEN the template SHALL contain "português" directives and all placeholders SHALL be filled

#### Scenario: Portuguese query handled end-to-end

- GIVEN user queries "Qual é o sentimento para PETR4?"
- WHEN the prompt is rendered with language="pt"
- THEN the LLM SHALL receive instructions to respond in Portuguese
- AND data section stripping SHALL recognize Portuguese headers ("Dados de Preço")

### Requirement: REQ-SCP-004 — Executive Structure

The prompt SHALL mandate a three-section narrative structure — Summary, Context & Catalysts, Outlook — with a hard prohibition on bullet lists of data.

#### Scenario: Structure enforced

- GIVEN the prompt is sent to the LLM
- WHEN the LLM responds
- THEN the response SHALL follow narrative executive structure
- AND it SHALL NOT contain data-category section headers
