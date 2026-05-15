"use client"

import { CryptoPriceCard } from "./CryptoPriceCard"
import { MacroIndicator } from "./MacroIndicator"
import { DataTable } from "./DataTable"
import { CalcResult } from "./CalcResult"
import { TimeSeriesChart } from "./TimeSeriesChart"
import type { WidgetData } from "@/lib/widgetParser"

interface WidgetRendererProps {
  widget: WidgetData
}

export function WidgetRenderer({ widget }: WidgetRendererProps) {
  switch (widget.type) {
    case "crypto":
      return <CryptoPriceCard data={widget.data} />
    case "macro":
      return <MacroIndicator data={widget.data} />
    case "table":
      return <DataTable data={widget.data} />
    case "calc":
      return <CalcResult data={widget.data} />
    case "chart":
      return <TimeSeriesChart
        data={widget.data.data || []}
        xKey={widget.data.xKey || "date"}
        yKey={widget.data.yKey || "value"}
        title={widget.data.title}
        type={widget.data.type || "line"}
        color={widget.data.color}
      />
    default:
      return (
        <p className="text-sm text-muted-foreground italic">
          Unknown widget: {widget.type}
        </p>
      )
  }
}
