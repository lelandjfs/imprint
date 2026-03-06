"""Conversation memory management."""

from typing import Dict, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


class ConversationMemoryStore:
    """In-memory store for conversation histories."""

    def __init__(self):
        self._store: Dict[str, List[BaseMessage]] = {}

    def get_messages(self, session_id: str) -> List[BaseMessage]:
        """Get conversation history for a session."""
        return self._store.get(session_id, [])

    def add_user_message(self, session_id: str, message: str):
        """Add a user message to the conversation."""
        if session_id not in self._store:
            self._store[session_id] = []
        self._store[session_id].append(HumanMessage(content=message))

    def add_ai_message(self, session_id: str, message: str):
        """Add an AI message to the conversation."""
        if session_id not in self._store:
            self._store[session_id] = []
        self._store[session_id].append(AIMessage(content=message))

    def clear_session(self, session_id: str):
        """Clear conversation history for a session."""
        if session_id in self._store:
            del self._store[session_id]


# Global memory store instance
memory_store = ConversationMemoryStore()
