"""
Conversation Memory - Session-Scoped Conversation Memory
===================================================

Session-scoped memory for tracking conversation history.
Stores user queries and assistant responses within a session.

Usage:
    memory = ConversationMemory()
    memory.add_user_message("What about AAPL?")
    memory.add_ai_message("AAPL went up 3%")
    history = memory.get_history()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Message:
    """Single message in conversation history."""

    role: str  # "user" | "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    tool_calls: list[dict[str, Any]] | None = None


class ConversationMemory:
    """
    Session-scoped conversation memory.

    Responsibilities:
    - Track user queries and assistant responses
    - Provide history for context in ReAct loop
    - Clear memory at session end

    Note: This is session-scoped only (not persisted to disk).
    For persistence, consider extending with database storage.

    Usage:
        memory = ConversationMemory()
        memory.add_user_message("What about AAPL?")
        history = memory.get_history()
    """

    def __init__(self, max_turns: int = 20) -> None:
        """
        Initialize conversation memory.

        Args:
            max_turns: Maximum number of conversation turns to keep
        """
        self.max_turns = max_turns
        self.messages: list[Message] = []

    def add_user_message(self, content: str) -> None:
        """
        Add a user message to history.

        Args:
            content: User's query
        """
        self.messages.append(Message(role="user", content=content))
        self._trim_history()

    def add_ai_message(
        self,
        content: str,
        tool_calls: list[dict[str, Any]] | None = None,
    ) -> None:
        """
        Add an assistant message to history.

        Args:
            content: Assistant's response
            tool_calls: Optional tool calls made during reasoning
        """
        self.messages.append(
            Message(role="assistant", content=content, tool_calls=tool_calls)
        )
        self._trim_history()

    def get_history(self) -> list[dict[str, str]]:
        """
        Get conversation history as list of dicts.

        Returns:
            List of dicts with keys: role, content, timestamp
        """
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
            }
            for msg in self.messages
        ]

    def get_recent_turns(self, n: int = 5) -> list[dict[str, str]]:
        """
        Get the most recent n turns.

        Args:
            n: Number of recent turns to return

        Returns:
            List of recent messages
        """
        start_idx = max(0, len(self.messages) - (n * 2))
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
            }
            for msg in self.messages[start_idx:]
        ]

    def get_context_string(self) -> str:
        """
        Get conversation history as a formatted string for prompting.

        Returns:
            Formatted string with recent conversation
        """
        if not self.messages:
            return "No conversation history."

        recent = self.get_recent_turns(n=3)
        lines = []
        for msg in recent:
            role_prefix = "User" if msg["role"] == "user" else "Assistant"
            lines.append(f"{role_prefix}: {msg['content']}")

        return "\n".join(lines)

    def clear(self) -> None:
        """Clear all conversation history."""
        self.messages = []

    def _trim_history(self) -> None:
        """Trim history to max_turns."""
        if len(self.messages) > self.max_turns * 2:
            self.messages = self.messages[-(self.max_turns * 2):]


__all__ = [
    "ConversationMemory",
]