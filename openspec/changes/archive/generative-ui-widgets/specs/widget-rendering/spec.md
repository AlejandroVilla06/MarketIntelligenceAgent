# widget-rendering Specification

## Purpose

Frontend pipeline that parses `[WIDGET:type]{json}[/WIDGET]` markers from LLM streaming responses and renders visual data widgets (CryptoPriceCard, MacroIndicator, DataTable, CalcResult) with skeleton loading states, flicker-free streaming, and buffer safety.

## Requirements

| ID | Requirement |
|----|-------------|
| R1 | **Widget Marker Format**: The system SHALL parse `[WIDGET:type]{json}[/WIDGET]` markers embedded in LLM responses. Supported types SHALL be: `crypto`, `macro`, `table`, `calc`. JSON SHALL be valid. Markers SHALL be self-contained (no external data fetches). |
| R2 | **Flicker-free Streaming Parser**: The parser SHALL render non-marker text immediately. On detecting `[WIDGET:`, the parser SHALL display a skeleton placeholder (animated pulse, same dimensions) and buffer tokens until `[/WIDGET]`. On close: parse JSON, render widget, replace skeleton. |
| R3 | **Buffer Safety**: The parser SHALL enforce MAX_WIDGET_TOKENS (2000) and WIDGET_TIMEOUT (5s). If either limit exceeded without `[/WIDGET]`, the buffer SHALL flush as raw text. |
| R4 | **CryptoPriceCard Widget**: SHALL display cryptocurrency name, symbol, USD price, 24h change (green for positive, red for negative), market cap (billions), and a mini SVG polyline sparkline. SHALL use shadcn Card. SHALL show skeleton placeholder during loading. |
| R5 | **MacroIndicator Widget**: SHALL display indicator name, current value, unit, date, and directional arrow (up/down based on change). SHALL use shadcn Card. SHALL show skeleton placeholder during loading. |
| R6 | **DataTable Widget**: SHALL display tabular data with headers and rows. SHALL be responsive with horizontal scroll at viewports below 768px. SHALL use shadcn Table. Skeleton SHALL render rows of grey animated pulses. |
| R7 | **CalcResult Widget**: SHALL display formula name, inputs, result, and interpretation text. SHALL use shadcn Card. |
| R8 | **Error Handling**: Invalid JSON in a marker SHALL render as a raw `<code>` block (no crash). Unknown widget types SHALL render as raw text. Nested markers SHALL NOT be supported (first `[/WIDGET]` closes the marker). |

## Scenarios

### R1: Widget Marker Format

- GIVEN an LLM response contains `[WIDGET:crypto]{"symbol":"BTC","price":81372.18}[/WIDGET]`
- WHEN the parser processes the content
- THEN it extracts a widget segment of type `crypto` with parsed JSON `{symbol: "BTC", price: 81372.18}`

- GIVEN a marker with type `unknown`
- WHEN the parser encounters `[WIDGET:chart]{...}[/WIDGET]`
- THEN the segment is classified as raw text, not a widget

### R2: Flicker-free Streaming Parser

- GIVEN the stream emits `"Bitcoin is currently trading at [WIDGET:crypto]{"symbol":"BTC","price":81372.18,"change24h":2.34}[/WIDGET] with strong volume"`
- WHEN the parser processes tokens sequentially
- THEN `"Bitcoin is currently trading at "` renders immediately as text
- AND on reaching `[WIDGET:crypto]`, a skeleton Card placeholder appears
- AND on reaching `[/WIDGET]`, the skeleton is replaced by the rendered CryptoPriceCard
- AND `" with strong volume"` renders immediately as text after the widget

- GIVEN tokens arrive one at a time: `"Pri"`, `"ce:"`, `"$"`, `"81k"`
- WHEN no `[WIDGET:` is detected
- THEN each token renders immediately with no buffering delay

### R3: Buffer Safety

- GIVEN a stream contains `[WIDGET:crypto]{...` (start tag but never closed)
- WHEN the buffer accumulates more than 2000 tokens without `[/WIDGET]`
- THEN the entire buffered content flushes as raw text (no skeleton, no widget)

- GIVEN a stream contains `[WIDGET:macro]{...` (start tag but never closed)
- WHEN 5 seconds elapse since the opening marker was detected
- THEN the buffer flushes as raw text

### R4: CryptoPriceCard Widget

- GIVEN widget data `{symbol:"BTC", name:"Bitcoin", price:81372.18, change24h:2.34, marketCap:1612000000000}`
- WHEN the CryptoPriceCard renders
- THEN "Bitcoin" and "BTC" are displayed
- AND "$81,372.18" is displayed as the price
- AND "+2.34%" is displayed in green
- AND "Market Cap: $1.61T" is displayed
- AND a skeleton pulse placeholder appears during streaming, matching the card dimensions

- GIVEN widget data `{symbol:"ETH", price:3240.50, change24h:-5.12}`
- WHEN the CryptoPriceCard renders
- THEN "-5.12%" is displayed in red

### R5: MacroIndicator Widget

- GIVEN widget data `{indicator:"GDP", value:28271.844, unit:"Billions USD", date:"2025-01-01", previousValue:27957.448}`
- WHEN the MacroIndicator renders
- THEN "GDP" is displayed as the indicator name
- AND "28,271.844 Billions USD" is displayed
- AND "2025-01-01" is displayed as the date
- AND an upward arrow (↑) is displayed (value increased from previous)

- GIVEN `{indicator:"CPI", value:312.3, previousValue:314.1}`
- WHEN the MacroIndicator renders
- THEN a downward arrow (↓) is displayed (value decreased)

### R6: DataTable Widget

- GIVEN widget data `{headers:["Rank","Name","Price"], rows:[["1","Bitcoin","$81,372"],["2","Ethereum","$3,241"]]}`
- WHEN the DataTable renders
- THEN a table appears with header row "Rank | Name | Price"
- AND two data rows follow
- AND skeleton rows of grey pulses appear during loading

- GIVEN viewport width is 400px
- WHEN the DataTable renders
- THEN the table scrolls horizontally without breaking the layout

### R7: CalcResult Widget

- GIVEN widget data `{formula:"NPV", inputs:{"rate":"10%","cashFlows":"$100 x 5"}, result:"-$20.92", interpretation:"Negative NPV: Project destroys value"}`
- WHEN the CalcResult renders
- THEN "NPV" is displayed as the formula name
- AND inputs `rate: 10%, cashFlows: $100 x 5` are shown
- AND result "-$20.92" is highlighted
- AND "Negative NPV: Project destroys value" is displayed as interpretation

### R8: Error Handling

- GIVEN a marker `[WIDGET:crypto]{invalid json}[/WIDGET]`
- WHEN the parser attempts to parse the JSON
- THEN the marker content renders as a raw `<code>` block with the malformed JSON visible
- AND no crash or blank space occurs

- GIVEN nested markers `[WIDGET:crypto]{...[WIDGET:macro]{...}[/WIDGET]...}[/WIDGET]`
- WHEN the parser encounters the first `[/WIDGET]`
- THEN the marker closes at that point; inner markers are treated as raw text
