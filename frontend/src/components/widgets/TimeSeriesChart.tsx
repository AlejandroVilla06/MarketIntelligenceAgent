"use client"

import { useMemo } from "react"
import {
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts"
import { Skeleton } from "@/components/ui/skeleton"
import { useThemeColors } from "@/hooks/useThemeColors"

interface ChartDataPoint {
  [key: string]: string | number
}

interface TimeSeriesChartProps {
  data: ChartDataPoint[]
  xKey: string
  yKey: string
  title?: string
  type?: "line" | "area"
  color?: string
  isLoading?: boolean
}

function formatValue(val: number): string {
  if (val >= 1_000_000_000) return `$${(val / 1_000_000_000).toFixed(1)}B`
  if (val >= 1_000_000) return `$${(val / 1_000_000).toFixed(1)}M`
  if (val >= 1_000) return `$${(val / 1_000).toFixed(1)}K`
  return `$${val.toFixed(2)}`
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border bg-background p-2 shadow-md text-xs">
      <p className="text-muted-foreground mb-1">{label}</p>
      <p className="font-medium" style={{ color: payload[0].color }}>
        {formatValue(payload[0].value as number)}
      </p>
    </div>
  )
}

export function TimeSeriesChart({
  data, xKey, yKey, title, type = "line", color, isLoading
}: TimeSeriesChartProps) {
  const themeColors = useThemeColors()
  const chartColor = color || themeColors.primary

  if (isLoading) {
    return (
      <div className="space-y-3 p-4">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-[250px] w-full rounded-lg" />
      </div>
    )
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[250px] text-sm text-muted-foreground">
        No hay datos disponibles
      </div>
    )
  }

  const ChartComponent = type === "area" ? AreaChart : LineChart
  const DataComponent = type === "area" ? Area : Line
  const dataProps = type === "area"
    ? { type: "monotone" as const, fill: chartColor + "20", stroke: chartColor }
    : { type: "monotone" as const, stroke: chartColor }

  return (
    <div className="w-full">
      {title && (
        <h4 className="text-sm font-medium mb-2 text-foreground">{title}</h4>
      )}
      <ResponsiveContainer width="100%" height={250}>
        <ChartComponent data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={themeColors.muted + "30"} />
          <XAxis
            dataKey={xKey}
            tick={{ fontSize: 11, fill: themeColors.muted }}
            axisLine={{ stroke: themeColors.muted + "30" }}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 11, fill: themeColors.muted }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v: number) => {
              if (v >= 1_000_000_000) return `${(v / 1_000_000_000).toFixed(0)}B`
              if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(0)}M`
              if (v >= 1_000) return `${(v / 1_000).toFixed(0)}K`
              return v.toString()
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <DataComponent
            {...dataProps}
            dataKey={yKey}
            dot={false}
            strokeWidth={2}
            activeDot={{ r: 4, strokeWidth: 2 }}
          />
        </ChartComponent>
      </ResponsiveContainer>
    </div>
  )
}
