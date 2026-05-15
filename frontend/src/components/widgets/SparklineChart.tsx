"use client"

interface SparklineProps {
  data: number[]
  width?: number
  height?: number
  color?: string
  positive?: boolean
}

export function SparklineChart({ data, width = 120, height = 40, color, positive }: SparklineProps) {
  if (!data || data.length < 2) return null

  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1

  const points = data
    .map((val, i) => {
      const x = (i / (data.length - 1)) * width
      const y = height - ((val - min) / range) * (height - 4) - 2
      return `${x},${y}`
    })
    .join(" ")

  const strokeColor =
    color ||
    (positive !== undefined ? (positive ? "#22c55e" : "#ef4444") : "#6366f1")

  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline
        fill="none"
        stroke={strokeColor}
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  )
}
