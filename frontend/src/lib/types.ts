export interface Message {
	id?: string
	role: "user" | "assistant"
	content: string
	timestamp?: string
}

export interface Conversation {
	id: string
	title: string
	messages: Message[]
	created_at?: string
	updated_at?: string
}

export interface ConversationListItem {
	id: string
	title: string
	message_count?: number
	created_at?: string
}
