"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { useRouter } from "next/navigation"
import { createClient } from "@/lib/supabase/client"
import { useAuthStore } from "@/stores/authStore"
import { useChatStore } from "@/stores/chatStore"
import type { ConversationListItem } from "@/lib/types"
import { api } from "@/lib/api"
import { MessageList } from "@/components/MessageList"
import { ChatInput } from "@/components/ChatInput"
import { Header } from "@/components/Header"
import { ConversationHistory } from "@/components/ConversationHistory"
import { Sheet, SheetContent } from "@/components/ui/sheet"
import { Clock } from "lucide-react"

export default function ChatPage() {
  const router = useRouter()
  const { user, loading, setUser } = useAuthStore()
  const {
    conversations,
    currentConversation,
    messages,
    isStreaming,
    streamingContent,
    setConversations,
    setCurrentConversation,
    addMessage,
    setStreaming,
    appendStreamToken,
    resetStreaming,
  } = useChatStore()

  const [hasMore, setHasMore] = useState(true)
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  const [leftOpen, setLeftOpen] = useState(false)
  const pageRef = useRef(1)
  const PAGE_SIZE = 20

  useEffect(() => {
    const supabase = createClient()
    supabase.auth.getUser().then(({ data: { user } }) => {
      if (!user) {
        router.push("/login")
        return
      }
      setUser(user)
      loadConversations()
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function loadConversations(reset = true) {
    try {
      setIsLoadingHistory(true)
      if (reset) {
        pageRef.current = 1
      }
      const page = pageRef.current
      const offset = (page - 1) * PAGE_SIZE
      const convs = await api.conversations.list(offset, PAGE_SIZE)
      if (reset) {
        setConversations(convs)
      } else {
        // Append for pagination — read current from store
        const current = useChatStore.getState().conversations
        setConversations([...current, ...convs])
      }
      setHasMore(convs.length >= PAGE_SIZE)
    } catch (err) {
      console.error("Failed to load conversations:", err)
    } finally {
      setIsLoadingHistory(false)
    }
  }

  const handleLoadMore = useCallback(async () => {
    if (isLoadingHistory || !hasMore) return
    pageRef.current += 1
    await loadConversations(false)
  }, [isLoadingHistory, hasMore])

  const handleNewChat = useCallback(async () => {
    try {
      const conv = await api.conversations.create()
      setCurrentConversation({ id: conv.id, title: "Nueva conversación", messages: [] })
      await loadConversations()
    } catch (err) {
      console.error("Failed to create conversation:", err)
    }
  }, [setCurrentConversation, loadConversations])

  const handleSelectConversation = useCallback(async (id: string) => {
    try {
      const conv = await api.conversations.get(id)
      setCurrentConversation(conv)
    } catch (err) {
      console.error("Failed to select conversation:", err)
    }
  }, [setCurrentConversation, loadConversations])

  const handleDeleteConversation = useCallback(async (id: string) => {
    try {
      await api.conversations.delete(id)
      if (currentConversation?.id === id) {
        setCurrentConversation(null)
      }
      await loadConversations()
    } catch (err) {
      console.error("Failed to delete conversation:", err)
    }
  }, [currentConversation?.id, setCurrentConversation, loadConversations])

  const handleSend = useCallback(
    async (query: string) => {
      if (!query.trim() || isStreaming) return

      const userMessage = { role: "user" as const, content: query }
      addMessage(userMessage)
      setStreaming(true)

      await api.chat.stream(
        query,
        currentConversation?.id,
        (token) => appendStreamToken(token),
        () => {
          const fullContent = useChatStore.getState().streamingContent
          addMessage({ role: "assistant", content: fullContent })
          resetStreaming()
          loadConversations()
        },
        (error) => {
          addMessage({ role: "assistant", content: `Error: ${error}` })
          resetStreaming()
        }
      )
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [currentConversation?.id, isStreaming]
  )

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" />
      </div>
    )
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Left Sidebar — historial de conversaciones */}
      <aside className="hidden lg:block w-80 border-r bg-background transition-all duration-300">
        <ConversationHistory
          conversations={conversations}
          activeId={currentConversation?.id}
          onSelect={handleSelectConversation}
          onDelete={handleDeleteConversation}
          onNew={handleNewChat}
          userEmail={user?.email || undefined}
          isLoading={isLoadingHistory}
          hasMore={hasMore}
          onLoadMore={handleLoadMore}
        />
      </aside>

      {/* Mobile left sidebar trigger */}
      <Sheet open={leftOpen} onOpenChange={setLeftOpen}>
        <SheetContent side="left" className="w-80 p-0">
          <ConversationHistory
            conversations={conversations}
            activeId={currentConversation?.id}
            onSelect={(id) => { handleSelectConversation(id); setLeftOpen(false) }}
            onDelete={handleDeleteConversation}
            onNew={handleNewChat}
            userEmail={user?.email || undefined}
            isLoading={isLoadingHistory}
            hasMore={hasMore}
            onLoadMore={handleLoadMore}
          />
        </SheetContent>
      </Sheet>

      {/* Chat Area */}
      <div className="flex-1 min-w-0 flex flex-col transition-all duration-300">
        <Header onToggleHistory={() => setLeftOpen(true)} />
        <MessageList
          messages={messages}
          streamingContent={isStreaming ? streamingContent : undefined}
        />
        <ChatInput onSend={handleSend} disabled={isStreaming} />
      </div>
    </div>
  )
}
