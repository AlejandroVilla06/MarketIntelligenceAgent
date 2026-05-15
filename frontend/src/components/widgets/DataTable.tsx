"use client"

import { useState, useMemo } from "react"
import { Skeleton } from "@/components/ui/skeleton"

interface TableData {
  columns: string[]
  rows: (string | number)[][]
}

interface DataTableProps {
  data?: TableData
  isLoading?: boolean
  title?: string
}

type SortDir = "asc" | "desc" | null

export function DataTable({ data, isLoading, title }: DataTableProps) {
  const [sortCol, setSortCol] = useState<number | null>(null)
  const [sortDir, setSortDir] = useState<SortDir>(null)

  const sortedRows = useMemo(() => {
    if (!data?.rows || sortCol === null || !sortDir) return data?.rows || []
    return [...data.rows].sort((a, b) => {
      const aVal = a[sortCol]
      const bVal = b[sortCol]
      if (typeof aVal === "number" && typeof bVal === "number") {
        return sortDir === "asc" ? aVal - bVal : bVal - aVal
      }
      const aStr = String(aVal).toLowerCase()
      const bStr = String(bVal).toLowerCase()
      return sortDir === "asc" ? aStr.localeCompare(bStr) : bStr.localeCompare(aStr)
    })
  }, [data, sortCol, sortDir])

  function handleSort(colIndex: number) {
    if (sortCol === colIndex) {
      if (sortDir === "asc") setSortDir("desc")
      else if (sortDir === "desc") { setSortCol(null); setSortDir(null) }
    } else {
      setSortCol(colIndex)
      setSortDir("asc")
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-2 p-4">
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-8 w-full" />
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="w-full overflow-x-auto">
      {title && <h4 className="text-sm font-medium mb-2">{title}</h4>}
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-muted-foreground">
            {data.columns.map((col, i) => (
              <th
                key={i}
                onClick={() => handleSort(i)}
                className="text-left py-2 px-2 font-medium cursor-pointer hover:text-foreground transition-colors select-none"
              >
                <div className="flex items-center gap-1">
                  {col}
                  {sortCol === i && (
                    <span className="text-xs">{sortDir === "asc" ? "▲" : "▼"}</span>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedRows.map((row, i) => (
            <tr key={i} className="border-b last:border-0 hover:bg-muted/50">
              {row.map((cell, j) => (
                <td key={j} className="py-2 px-2">
                  {typeof cell === "number" ? cell.toLocaleString() : cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
