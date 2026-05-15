"use client"

import { useState, useMemo, useRef, useEffect } from "react"
import { MessageSquare, Plus, LogOut } from "lucide-react"
import type { ConversationListItem } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ConversationSearch } from "./ConversationSearch"
import { ConversationItem } from "./ConversationItem"

interface ConversationHistoryProps {
  conversations: ConversationListItem[]
  activeId?: string
  onSelect: (id: string) => void
  onDelete: (id: string) => void
  onNew: () => void
  userEmail?: string
  onLogout?: () => void
  isLoading?: boolean
  hasMore?: boolean
  onLoadMore?: () => void
}

type GroupKey = "Hoy" | "Ayer" | "Esta semana" | "Anteriores"

function groupByDate(convs: ConversationListItem[]): [GroupKey, ConversationListItem[]][] {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const groups = new Map<GroupKey, ConversationListItem[]>()

  for (const conv of convs) {
    const date = new Date(conv.created_at ?? 0)
    const convDay = new Date(date.getFullYear(), date.getMonth(), date.getDate())
    const diffDays = Math.floor((today.getTime() - convDay.getTime()) / 86400000)

    let key: GroupKey
    if (diffDays === 0) key = "Hoy"
    else if (diffDays === 1) key = "Ayer"
    else if (diffDays <= 7) key = "Esta semana"
    else key = "Anteriores"

    if (!groups.has(key)) groups.set(key, [])
    groups.get(key)!.push(conv)
  }

  const order: GroupKey[] = ["Hoy", "Ayer", "Esta semana", "Anteriores"]
  return order.filter(k => groups.has(k)).map(k => [k, groups.get(k)!])
}

function LoadingSkeleton() {
  return (
    <div className="space-y-4 p-4">
      <Skeleton className="h-8 w-full rounded-lg" />
      <div className="space-y-2">
        {[1, 2, 3, 4, 5].map((i) => (
          <Skeleton key={i} className="h-12 w-full rounded-lg" />
        ))}
      </div>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center mb-4">
        <MessageSquare className="h-6 w-6 text-muted-foreground" />
      </div>
      <h3 className="text-sm font-medium mb-1">No hay conversaciones</h3>
      <p className="text-xs text-muted-foreground max-w-[200px]">
        Tus conversaciones aparecerán aquí. Iniciá un nuevo chat para comenzar.
      </p>
    </div>
  )
}

export function ConversationHistory({
  conversations, activeId, onSelect, onDelete, onNew,
  userEmail, onLogout, isLoading, hasMore, onLoadMore,
}: ConversationHistoryProps) {
  const [search, setSearch] = useState("")
  const sentinelRef = useRef<HTMLDivElement>(null)

  // Filter by search
  const filtered = useMemo(() => {
    if (!search.trim()) return conversations
    const q = search.toLowerCase().trim()
    return conversations.filter(c => c.title.toLowerCase().includes(q))
  }, [conversations, search])

  // Group by date
  const grouped = useMemo(() => groupByDate(filtered), [filtered])

  // Infinite scroll observer
  useEffect(() => {
    if (!hasMore || !onLoadMore) return
    const el = sentinelRef.current
    if (!el) return

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) onLoadMore()
      },
      { threshold: 0.1 }
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [hasMore, onLoadMore, filtered.length])

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header + Search */}
      <div className="p-4 border-b space-y-3">
        <h2 className="text-sm font-semibold text-foreground">Historial</h2>
        <ConversationSearch value={search} onChange={setSearch} />
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-4">
        {isLoading ? (
          <LoadingSkeleton />
        ) : grouped.length === 0 ? (
          search.trim() ? (
            <div className="text-center py-12">
              <p className="text-sm text-muted-foreground">No se encontraron conversaciones</p>
            </div>
          ) : (
            <EmptyState />
          )
        ) : (
          grouped.map(([group, convs]) => (
            <div key={group}>
              <h3 className="text-xs font-medium text-muted-foreground px-3 mb-1 uppercase tracking-wide">
                {group}
              </h3>
              <div className="space-y-0.5">
                {convs.map((conv) => (
                  <ConversationItem
                    key={conv.id}
                    conversation={conv}
                    isActive={conv.id === activeId}
                    onSelect={onSelect}
                    onDelete={onDelete}
                  />
                ))}
              </div>
            </div>
          ))
        )}

        {/* Infinite scroll sentinel */}
        {hasMore && !isLoading && (
          <div ref={sentinelRef} className="h-4 flex items-center justify-center">
            <div className="h-4 w-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>

      {/* Footer: New Chat + User */}
      <div className="border-t p-3 space-y-2">
        <Button onClick={onNew} className="w-full justify-start gap-2" variant="outline" size="sm">
          <Plus className="h-4 w-4" />
          Nuevo Chat
        </Button>
        {userEmail && (
          <div className="flex items-center gap-2 px-2 py-1.5">
            <div className="flex-1 min-w-0">
              <p className="text-xs text-muted-foreground truncate">{userEmail}</p>
            </div>
            {onLogout && (
              <button onClick={onLogout} className="p-1 hover:text-destructive transition-colors">
                <LogOut className="h-4 w-4" />
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
