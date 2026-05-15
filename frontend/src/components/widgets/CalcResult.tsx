"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

interface CalcData {
  formula: string
  inputs?: Record<string, any>
  result: number | string
  interpretation?: string
}

interface CalcResultProps {
  data?: CalcData
  isLoading?: boolean
}

export function CalcResult({ data, isLoading }: CalcResultProps) {
  if (isLoading) {
    return (
      <Card className="w-full max-w-sm">
        <CardContent className="p-4 space-y-3">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-8 w-20" />
          <Skeleton className="h-4 w-40" />
        </CardContent>
      </Card>
    )
  }

  if (!data) return null

  return (
    <Card className="w-full max-w-sm bg-muted/30">
      <CardContent className="p-4">
        <div className="text-xs font-mono text-muted-foreground mb-1">{data.formula}</div>
        <div className="text-2xl font-bold mb-1">
          {typeof data.result === "number"
            ? data.result.toLocaleString(undefined, { maximumFractionDigits: 4 })
            : data.result}
        </div>
        {data.interpretation && (
          <p className="text-sm text-muted-foreground">{data.interpretation}</p>
        )}
      </CardContent>
    </Card>
  )
}
