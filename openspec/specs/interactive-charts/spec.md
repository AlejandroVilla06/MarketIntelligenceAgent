# interactive-charts Specification

## Purpose

Recharts-based TimeSeriesChart widget consuming `[WIDGET:chart]` markers with Tailwind theme colors, responsive container, and interactive tooltip. Enhanced DataTable with column sorting.

## Requirements

| ID | Requirement |
|----|-------------|
| R1 | **TimeSeriesChart Rendering**: The system SHALL render a Recharts `LineChart` (or `AreaChart` per `type` field) when the `[WIDGET:chart]` marker is detected. The chart SHALL use Tailwind CSS variable colors: `hsl(var(--chart-1))` for the line, `hsl(var(--muted))` for grid, `hsl(var(--foreground))` for axis labels. SHALL wrap in `ResponsiveContainer` (width="100%", height={250}). SHALL show a Recharts `<Tooltip />` on hover with date and formatted value. |
| R2 | **Chart Data Format**: The `[WIDGET:chart]` JSON SHALL include: `type` (`"line"` | `"area"`), `data` (array of objects), `xKey` (string), `yKey` (string), `title` (string). Optional: `xLabel`, `yLabel`, `color`. The system SHALL handle empty `data` arrays by rendering "No data available" text instead of an empty chart. |
| R3 | **DataTable Enhancements**: The DataTable SHALL support column sorting on header click (asc → desc → none). The active sort column SHALL display a direction indicator (▲/▼). Sorting SHALL be client-side and case-insensitive for strings. The sorting icon SHALL use muted color when inactive and foreground color when active. |

## Scenarios

### R1: TimeSeriesChart Rendering

- GIVEN an LLM response contains `[WIDGET:chart]{"type":"line","data":[{"date":"2026-01-01","price":100},{"date":"2026-01-02","price":105}],"xKey":"date","yKey":"price","title":"BTC/USD"}[/WIDGET]`
- WHEN the WidgetRenderer parses the marker
- THEN a Recharts `LineChart` renders inside a `ResponsiveContainer` (width="100%", height={250})
- AND the line color matches `hsl(var(--chart-1))`
- AND hovering shows a tooltip with the date and price value
- AND the chart title "BTC/USD" is displayed above the chart

- GIVEN the same marker but with `"type":"area"`
- WHEN the WidgetRenderer routes to TimeSeriesChart
- THEN a Recharts `AreaChart` renders with a filled gradient area

- GIVEN an empty data array `"data":[]` in the chart marker
- WHEN the TimeSeriesChart renders
- THEN "No data available" is displayed centered in the chart area
- AND no empty axes or grid lines are shown

- GIVEN viewport width is 400px
- WHEN the TimeSeriesChart renders
- THEN the chart scales to fit 100% of the container width
- AND the tooltip remains usable on touch devices

### R2: Chart Data Format

- GIVEN a `[WIDGET:chart]` marker with invalid JSON (e.g., missing `data` field)
- WHEN the parser processes the marker
- THEN the marker content renders as raw `<code>` block (no crash)
- AND no blank space or broken chart appears

- GIVEN a `[WIDGET:chart]` marker with negative y-values
- WHEN the chart renders
- THEN the Y-axis includes the negative range
- AND the line/area renders correctly extending below zero

### R3: DataTable Enhancements

- GIVEN a DataTable with columns "Rank", "Name", "Price"
- WHEN user clicks the "Price" column header
- THEN rows sort ascending by price
- AND a ▲ indicator appears next to "Price"

- GIVEN rows sorted ascending by "Price"
- WHEN user clicks "Price" header again
- THEN rows sort descending by price
- AND the indicator changes to ▼

- GIVEN rows sorted by "Price"
- WHEN user clicks "Price" header a third time
- THEN sorting resets to original row order
- AND no direction indicator is shown

- GIVEN strings "ETH" and "btc" (mixed case) in a column
- WHEN the column is sorted ascending
- THEN "btc" appears before "ETH" (case-insensitive sort)