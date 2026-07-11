import logging
from typing import Dict, Any, List

logger = logging.getLogger("conversation_memory")

class ConversationMemory:
    # In-memory session store: { session_id: { "history": [ (role, content) ], "last_bill_id": int } }
    _sessions: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def get_or_create_session(session_id: str) -> Dict[str, Any]:
        """
        Retrieves existing session payload or initializes a new one.
        """
        if session_id not in ConversationMemory._sessions:
            ConversationMemory._sessions[session_id] = {
                "history": [],
                "last_bill_id": None
            }
        return ConversationMemory._sessions[session_id]

    @staticmethod
    def add_message(session_id: str, role: str, content: str) -> None:
        """
        Appends a message to the conversation history, keeping only the last 10 turns for token economy.
        """
        session = ConversationMemory.get_or_create_session(session_id)
        session["history"].append((role, content))
        if len(session["history"]) > 20:  # 10 turns (user + assistant)
            session["history"] = session["history"][-20:]

    @staticmethod
    def set_last_bill(session_id: str, bill_id: int) -> None:
        """
        Associates the last active bill context to the session.
        """
        if bill_id is not None:
            session = ConversationMemory.get_or_create_session(session_id)
            session["last_bill_id"] = bill_id

    @staticmethod
    def get_last_bill(session_id: str) -> int:
        """
        Retrieves the last active bill context from the session.
        """
        session = ConversationMemory.get_or_create_session(session_id)
        return session.get("last_bill_id")

    @staticmethod
    def get_history_as_text(session_id: str) -> str:
        """
        Formats conversation history as a transcript block for prompt builder context.
        """
        session = ConversationMemory.get_or_create_session(session_id)
        history = session.get("history", [])
        if not history:
            return ""
            
        transcript = []
        for role, text in history:
            label = "User" if role == "user" else "Assistant"
            transcript.append(f"{label}: {text}")
        return "\n".join(transcript)

    @staticmethod
    def clear_session(session_id: str) -> None:
        """
        Deletes the session data.
        """
        if session_id in ConversationMemory._sessions:
            del ConversationMemory._sessions[session_id]
            logger.info(f"Session {session_id} memory cleared.")
