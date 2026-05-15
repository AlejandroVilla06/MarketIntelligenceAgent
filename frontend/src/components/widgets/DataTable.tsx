"use client"

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

export function DataTable({ data, isLoading, title }: DataTableProps) {
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
              <th key={i} className="text-left py-2 px-2 font-medium">{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.rows.map((row, i) => (
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
