# widget-markers Specification

## Purpose

Backend marker format specification and sub-orchestrator prompt templates for emitting `[WIDGET:type]{json}[/WIDGET]` markers in LLM responses. Defines the JSON schema each sub-orchestrator SHALL use and the prompt instructions that guide the LLM to produce valid markers.

## Requirements

| ID | Requirement |
|----|-------------|
| R1 | **CryptoSubOrchestrator Markers**: The crypto sub-orchestrator SHALL append `[WIDGET:crypto]{json}[/WIDGET]` to its LLM response. JSON SHALL include: `symbol`, `name`, `price`, `change24h`, `marketCap`, `rank`. Optional: `change7d`, `volume24h`. Marker SHALL be placed at the end of the response. |
| R2 | **MacroSubOrchestrator Markers**: The macro sub-orchestrator SHALL append one `[WIDGET:macro]{json}[/WIDGET]` per indicator. JSON SHALL include: `indicator`, `value`, `unit`, `date`, `previousValue`. Optional: `source`. |
| R3 | **CalculationExecutor Markers**: The calculation executor SHALL append `[WIDGET:calc]{json}[/WIDGET]`. JSON SHALL include: `formula`, `inputs` (Record<string,string>), `result`, `interpretation`. |
| R4 | **Prompt Instructions**: LLM prompts SHALL include: "After your analysis, append a data marker in format `[WIDGET:type]{...json...}[/WIDGET]` where type is one of: crypto, macro, table, calc." The prompt SHALL include the exact JSON schema for each widget type. |

## Scenarios

### R1: CryptoSubOrchestrator Markers

- GIVEN a user query about Bitcoin price
- WHEN the CryptoSubOrchestrator LLM generates its response
- THEN the response SHALL end with a marker like: `[WIDGET:crypto]{"symbol":"BTC","name":"Bitcoin","price":81372.18,"change24h":2.34,"marketCap":1612000000000,"rank":1}[/WIDGET]`
- AND the marker JSON SHALL contain all required fields: symbol, name, price, change24h, marketCap, rank

- GIVEN the LLM returns price data for Ethereum
- WHEN the marker is appended
- THEN `change24h` is `-5.12` (negative value preserved, not absolute)

- GIVEN the CryptoSubOrchestrator handles a top-10 request
- WHEN the LLM generates a table response
- THEN it SHALL append a table marker: `[WIDGET:table]{"headers":["Rank","Name","Symbol","Price","24h"],"rows":[["1","Bitcoin","BTC","$81,372","+2.3%"]]}[/WIDGET]`

### R2: MacroSubOrchestrator Markers

- GIVEN a user query about US GDP
- WHEN the MacroSubOrchestrator LLM generates its response
- THEN the response SHALL include: `[WIDGET:macro]{"indicator":"GDP","value":28271.844,"unit":"Billions USD","date":"2025-01-01","previousValue":27957.448,"source":"FRED"}[/WIDGET]`
- AND the marker JSON SHALL contain indicator, value, unit, date, and previousValue

- GIVEN multiple indicators are requested (GDP, CPI, Unemployment)
- WHEN the LLM generates a combined response
- THEN one macro marker SHALL be appended per indicator
- AND each marker is independently parseable

### R3: CalculationExecutor Markers

- GIVEN a user requests NPV calculation with discount rate 10% and 5-year cash flows of $100
- WHEN the CalculationExecutor completes the computation
- THEN the response SHALL include: `[WIDGET:calc]{"formula":"NPV","inputs":{"rate":"10%","cashFlows":"$100 x 5 years"},"result":"-$20.92","interpretation":"Negative NPV: Project destroys value"}[/WIDGET]`

- GIVEN a Sharpe ratio calculation
- WHEN the executor returns the result
- THEN the marker SHALL contain `{"formula":"Sharpe Ratio","inputs":{"return":"12%","riskFree":"3%","stdDev":"8%"},"result":"1.125","interpretation":"Sharpe > 1: Good risk-adjusted return"}`

### R4: Prompt Instructions

- GIVEN the CryptoSubOrchestrator constructs its LLM prompt
- WHEN the system prompt is assembled
- THEN it SHALL include: `After your analysis, append a data marker: [WIDGET:crypto]{"symbol":"...","name":"...","price":...,"change24h":...,"marketCap":...,"rank":...}[/WIDGET]`
- AND the JSON schema example SHALL use placeholder values matching the actual JSON structure

- GIVEN the MacroSubOrchestrator prompt
- WHEN the system prompt is assembled
- THEN it SHALL include the macro widget JSON schema: `{"indicator":"string","value":number,"unit":"string","date":"YYYY-MM-DD","previousValue":number}`
- AND SHALL instruct: `Append ONE [WIDGET:macro] marker per indicator discussed`

- GIVEN the LLM ignores the marker instruction
- WHEN no `[WIDGET:` is found in the response
- THEN the frontend SHALL render the response as plain text (no crash, no blank area)
