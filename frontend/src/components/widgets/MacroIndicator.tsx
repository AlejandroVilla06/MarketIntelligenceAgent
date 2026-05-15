"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"

interface MacroData {
  indicator: string
  value: number
  unit?: string
  date?: string
  previousValue?: number
}

interface MacroIndicatorProps {
  data?: MacroData
  isLoading?: boolean
}

export function MacroIndicator({ data, isLoading }: MacroIndicatorProps) {
  if (isLoading) {
    return (
      <Card className="w-full max-w-sm">
        <CardContent className="p-4 space-y-3">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-8 w-24" />
          <Skeleton className="h-4 w-20" />
        </CardContent>
      </Card>
    )
  }

  if (!data) return null

  const isUp = data.previousValue !== undefined ? data.value >= data.previousValue : true

  return (
    <Card className="w-full max-w-sm">
      <CardContent className="p-4">
        <div className="text-sm text-muted-foreground mb-1">{data.indicator}</div>
        <div className="text-2xl font-bold mb-1">
          {data.value?.toLocaleString()}
          {data.unit && <span className="text-sm font-normal ml-1">{data.unit}</span>}
        </div>
        <div className="flex items-center gap-2">
          {data.previousValue !== undefined && (
            <span className={cn("text-sm", isUp ? "text-green-500" : "text-red-500")}>
              {isUp ? "▲" : "▼"} {(data.value - data.previousValue).toFixed(1)}
            </span>
          )}
          {data.date && <span className="text-xs text-muted-foreground">{data.date}</span>}
        </div>
      </CardContent>
    </Card>
  )
}
