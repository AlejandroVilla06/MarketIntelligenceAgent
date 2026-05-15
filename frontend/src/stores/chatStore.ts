import { create } from "zustand"
import type { Conversation, ConversationListItem, Message } from "@/lib/types"

interface ChatState {
  conversations: ConversationListItem[]
  currentConversation: Conversation | null
  messages: Message[]
  isStreaming: boolean
  streamingContent: string

  setConversations: (conversations: ConversationListItem[]) => void
  setCurrentConversation: (conv: Conversation | null) => void
  addMessage: (message: Message) => void
  setStreaming: (streaming: boolean) => void
  setStreamingContent: (content: string) => void
  appendStreamToken: (token: string) => void
  resetStreaming: () => void
}

export const useChatStore = create<ChatState>((set) => ({
  conversations: [],
  currentConversation: null,
  messages: [],
  isStreaming: false,
  streamingContent: "",

  setConversations: (conversations) => set({ conversations }),
  setCurrentConversation: (conv) =>
    set({
      currentConversation: conv,
      messages: conv?.messages ?? [],
    }),
  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),
  setStreaming: (isStreaming) => set({ isStreaming }),
  setStreamingContent: (content) => set({ streamingContent: content }),
  appendStreamToken: (token) =>
    set((state) => ({
      streamingContent: state.streamingContent + token,
    })),
  resetStreaming: () => set({ isStreaming: false, streamingContent: "" }),
}))
