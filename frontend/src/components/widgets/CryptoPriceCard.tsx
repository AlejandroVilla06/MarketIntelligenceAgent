"use client"

import { Card, CardContent } from "@/components/ui/card"
import { SparklineChart } from "./SparklineChart"
import { cn } from "@/lib/utils"
import { Skeleton } from "@/components/ui/skeleton"

interface CryptoPriceData {
  symbol: string
  name?: string
  price: number
  change24h?: number
  marketCap?: number
  rank?: number
  sparkline?: number[]
}

interface CryptoPriceCardProps {
  data?: CryptoPriceData
  isLoading?: boolean
}

export function CryptoPriceCard({ data, isLoading }: CryptoPriceCardProps) {
  if (isLoading) {
    return (
      <Card className="w-full max-w-sm">
        <CardContent className="p-4 space-y-3">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-8 w-32" />
          <Skeleton className="h-4 w-40" />
        </CardContent>
      </Card>
    )
  }

  if (!data) return null

  const isPositive = data.change24h !== undefined ? data.change24h >= 0 : true

  return (
    <Card className="w-full max-w-sm border-l-4" style={{
      borderLeftColor: isPositive ? "#22c55e" : "#ef4444"
    }}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-2">
          <div>
            <span className="text-lg font-bold">{data.symbol}</span>
            {data.name && (
              <span className="text-sm text-muted-foreground ml-2">{data.name}</span>
            )}
          </div>
          {data.rank && (
            <span className="text-xs bg-muted px-2 py-0.5 rounded-full">
              #{data.rank}
            </span>
          )}
        </div>

        <div className="text-2xl font-bold mb-1">
          ${data.price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>

        <div className="flex items-center gap-4">
          {data.change24h !== undefined && (
            <span className={cn(
              "text-sm font-medium",
              isPositive ? "text-green-500" : "text-red-500"
            )}>
              {isPositive ? "▲" : "▼"} {Math.abs(data.change24h).toFixed(2)}%
            </span>
          )}
          {data.marketCap !== undefined && (
            <span className="text-xs text-muted-foreground">
              Cap: ${(data.marketCap / 1e9).toFixed(2)}B
            </span>
          )}
        </div>

        {data.sparkline && data.sparkline.length > 0 && (
          <div className="mt-2">
            <SparklineChart
              data={data.sparkline}
              width={200}
              height={36}
              positive={isPositive}
            />
          </div>
        )}
      </CardContent>
    </Card>
  )
}
