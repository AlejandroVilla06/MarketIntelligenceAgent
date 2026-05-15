"use client"

import type { ConversationListItem } from "@/lib/types"
import { Trash2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface ConversationItemProps {
  conversation: ConversationListItem
  isActive: boolean
  onSelect: (id: string) => void
  onDelete: (id: string) => void
}

export function ConversationItem({ conversation, isActive, onSelect, onDelete }: ConversationItemProps) {
  return (
    <button
      onClick={() => onSelect(conversation.id)}
      className={cn(
        "group w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all duration-150",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
        isActive
          ? "bg-primary/10 text-primary font-medium"
          : "hover:bg-muted text-muted-foreground hover:text-foreground"
      )}
    >
      <div className="flex items-center gap-2 min-w-0">
        <span className="flex-1 truncate">{conversation.title}</span>
        <span className="text-xs text-muted-foreground shrink-0 tabular-nums">
          {conversation.message_count}
        </span>
        <button
          onClick={(e) => { e.stopPropagation(); onDelete(conversation.id) }}
          className="opacity-0 group-hover:opacity-100 transition-opacity p-0.5 hover:text-destructive shrink-0"
          aria-label="Eliminar conversación"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>
    </button>
  )
}
