"use client"

import { memo, useState } from "react"
import type { ConversationListItem } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Plus, Trash2, Menu } from "lucide-react"

interface SidebarProps {
  conversations: ConversationListItem[]
  activeId?: string
  onSelect: (id: string) => void
  onDelete: (id: string) => void
  onNew: () => void
}

function SidebarContent({ conversations, activeId, onSelect, onDelete, onNew }: SidebarProps) {
  return (
    <div className="flex flex-col h-full">
      <div className="p-3 border-b">
        <Button onClick={onNew} className="w-full justify-start gap-2" variant="outline">
          <Plus className="h-4 w-4" />
          Nueva conversación
        </Button>
      </div>
      <nav className="flex-1 overflow-y-auto p-2 space-y-1">
        {conversations.length === 0 ? (
          <p className="text-xs text-muted-foreground text-center py-8">
            No hay conversaciones aún
          </p>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`group flex items-center gap-1 rounded-lg px-3 py-2 text-sm cursor-pointer transition-colors ${
                conv.id === activeId
                  ? "bg-primary/10 text-primary"
                  : "hover:bg-muted text-muted-foreground hover:text-foreground"
              }`}
              onClick={() => onSelect(conv.id)}
            >
              <span className="flex-1 truncate">{conv.title}</span>
              <button
                onClick={(e) => { e.stopPropagation(); onDelete(conv.id) }}
                className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:text-destructive"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))
        )}
      </nav>
      <div className="p-3 border-t text-xs text-muted-foreground text-center">
        Market Intelligence Agent
      </div>
    </div>
  )
}

export const Sidebar = memo(function Sidebar(props: SidebarProps) {
  const [open, setOpen] = useState(false)

  function wrappedOnSelect(id: string) {
    props.onSelect(id)
    setOpen(false)
  }

  return (
    <>
      {/* Mobile: Sheet (slide-over) */}
      <Sheet open={open} onOpenChange={setOpen}>
        <button
          onClick={() => setOpen(true)}
          className="md:hidden fixed top-3 left-3 z-50 inline-flex items-center justify-center rounded-md p-2 text-muted-foreground hover:bg-muted transition-colors"
        >
          <Menu className="h-5 w-5" />
        </button>
        <SheetContent side="left" className="w-72 p-0">
          <SidebarContent {...props} onSelect={wrappedOnSelect} />
        </SheetContent>
      </Sheet>

      {/* Desktop: fixed sidebar */}
      <aside className="w-72 border-r bg-muted/30 flex-col h-full hidden md:flex">
        <SidebarContent {...props} />
      </aside>
    </>
  )
})
