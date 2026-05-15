import { useCallback } from "react"
import { useChatStore } from "@/stores/chatStore"
import { api } from "@/lib/api"

export function useChat() {
  const {
    messages,
    isStreaming,
    streamingContent,
    addMessage,
    setStreaming,
    appendStreamToken,
    resetStreaming,
    currentConversation,
  } = useChatStore()

  const sendMessage = useCallback(
    async (query: string) => {
      if (!query.trim() || isStreaming) return

      addMessage({ role: "user", content: query })
      setStreaming(true)

      await api.chat.stream(
        query,
        currentConversation?.id,
        (token) => appendStreamToken(token),
        () => {
          const fullContent = useChatStore.getState().streamingContent
          addMessage({ role: "assistant", content: fullContent })
          resetStreaming()
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

  return {
    messages,
    isStreaming,
    streamingContent,
    sendMessage,
  }
}
