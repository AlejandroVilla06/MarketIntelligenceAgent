import { memo } from "react"
import dynamic from "next/dynamic"
import type { Message } from "@/lib/types"
import { parseMessage } from "@/lib/widgetParser"
import { WidgetRenderer } from "./widgets/WidgetRenderer"

const ReactMarkdown = dynamic(() => import("react-markdown"), {
  ssr: false,
  loading: () => <span className="animate-pulse" />,
})

interface ChatMessageProps {
  message: Message
  isStreaming?: boolean
}

export const ChatMessage = memo(function ChatMessage({ message, isStreaming }: ChatMessageProps) {
  const isUser = message.role === "user"

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-xs font-medium text-primary">
          AI
        </div>
      )}
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-primary text-primary-foreground rounded-br-sm"
            : "bg-muted rounded-bl-sm"
        }`}
      >
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="prose prose-sm dark:prose-invert max-w-none">
            {(() => {
              const segments = parseMessage(message.content)
              return segments.map((seg, i) => {
                if (seg.kind === "text") {
                  return <ReactMarkdown key={i}>{seg.content}</ReactMarkdown>
                }
                if (seg.kind === "widget" && seg.widgetData) {
                  return (
                    <div key={i} className="my-2">
                      <WidgetRenderer widget={seg.widgetData} />
                    </div>
                  )
                }
                return null
              })
            })()}
            {isStreaming && (
              <span className="inline-block w-2 h-4 bg-primary animate-pulse ml-0.5" />
            )}
          </div>
        )}
      </div>
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center text-xs font-medium text-primary-foreground">
          U
        </div>
      )}
    </div>
  )
})
