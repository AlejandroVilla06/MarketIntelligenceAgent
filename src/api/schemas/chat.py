from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User query")
    conversation_id: str | None = Field(None, description="Existing conversation ID")


class ChatResponse(BaseModel):
    response: str = Field(..., description="Agent response")
    conversation_id: str = Field(..., description="Conversation ID")


class Message(BaseModel):
    role: str = Field(..., description="user or assistant")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Conversation(BaseModel):
    id: str
    title: str = "Nueva conversación"
    messages: list[Message] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationListItem(BaseModel):
    id: str
    title: str
    message_count: int
    created_at: datetime
