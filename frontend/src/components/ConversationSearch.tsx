"use client"

import { Search } from "lucide-react"
import { cn } from "@/lib/utils"

interface ConversationSearchProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

export function ConversationSearch({ value, onChange, placeholder = "Buscar conversaciones..." }: ConversationSearchProps) {
  return (
    <div className="relative">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={cn(
          "w-full h-9 pl-9 pr-3 rounded-lg text-sm",
          "bg-muted/50 border border-border",
          "placeholder:text-muted-foreground",
          "focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent",
          "transition-all duration-200"
        )}
      />
    </div>
  )
}
