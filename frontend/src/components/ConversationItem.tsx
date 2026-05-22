"use client"

import { useState, useRef, useEffect } from "react"
import type { ConversationListItem } from "@/lib/types"
import { Trash2, PencilLine } from "lucide-react"
import { cn } from "@/lib/utils"

interface ConversationItemProps {
  conversation: ConversationListItem
  isActive: boolean
  onSelect: (id: string) => void
  onDelete: (id: string) => void
  onRename: (id: string, title: string) => void
}

export function ConversationItem({ conversation, isActive, onSelect, onDelete, onRename }: ConversationItemProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(conversation.title)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (isEditing) {
      inputRef.current?.focus()
      inputRef.current?.select()
    }
  }, [isEditing])

  function handleStartEdit(e: React.MouseEvent) {
    e.stopPropagation()
    setEditTitle(conversation.title)
    setIsEditing(true)
  }

  function handleFinishEdit() {
    const trimmed = editTitle.trim()
    if (trimmed && trimmed !== conversation.title) {
      onRename(conversation.id, trimmed)
    }
    setIsEditing(false)
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") {
      handleFinishEdit()
    } else if (e.key === "Escape") {
      setEditTitle(conversation.title)
      setIsEditing(false)
    }
  }

  return (
    <button
      onClick={() => !isEditing && onSelect(conversation.id)}
      className={cn(
        "group w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all duration-150",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
        isActive
          ? "bg-primary/10 text-primary font-medium"
          : "hover:bg-muted text-muted-foreground hover:text-foreground"
      )}
    >
      <div className="flex items-center gap-2 min-w-0">
        {isEditing ? (
          <input
            ref={inputRef}
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            onBlur={handleFinishEdit}
            onKeyDown={handleKeyDown}
            className="flex-1 min-w-0 bg-background border rounded px-1 py-0.5 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
          />
        ) : (
          <span className="flex-1 truncate">{conversation.title}</span>
        )}
        <span className="text-xs text-muted-foreground shrink-0 tabular-nums">
          {conversation.message_count}
        </span>
        {!isEditing && (
          <>
            <button
              onClick={handleStartEdit}
              className="opacity-0 group-hover:opacity-100 transition-opacity p-0.5 hover:text-primary shrink-0"
              aria-label="Renombrar conversación"
            >
              <PencilLine className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); onDelete(conversation.id) }}
              className="opacity-0 group-hover:opacity-100 transition-opacity p-0.5 hover:text-destructive shrink-0"
              aria-label="Eliminar conversación"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </>
        )}
      </div>
    </button>
  )
}
