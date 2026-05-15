"use client"

import { memo, useEffect, useRef } from "react"
import type { Message } from "@/lib/types"
import { ChatMessage } from "./ChatMessage"

interface MessageListProps {
  messages: Message[]
  streamingContent?: string
}

export const MessageList = memo(function MessageList({ messages, streamingContent }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, streamingContent])

  if (messages.length === 0 && !streamingContent) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center max-w-md px-4">
          <h2 className="text-2xl font-semibold mb-2 bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
            Market Intelligence Agent
          </h2>
          <p className="text-muted-foreground text-sm">
            Preguntá sobre acciones, noticias financieras o sentimiento del mercado.
            Te respondo en tu idioma.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
      {messages.map((msg, i) => (
        <ChatMessage key={`${msg.role}-${i}`} message={msg} />
      ))}
      {streamingContent && (
        <ChatMessage
          message={{ role: "assistant", content: streamingContent }}
          isStreaming
        />
      )}
      <div ref={bottomRef} />
    </div>
  )
})
