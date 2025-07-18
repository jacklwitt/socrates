from typing import Optional, List
from datetime import datetime, UTC
import json

# In-memory message store
messages: List[dict] = []

def log_message(speaker: str, text: str, reply_to: Optional[str] = None):
    """Log a new message with the current UTC timestamp."""
    message = {
        "speaker": speaker,
        "text": text,
        "timestamp": datetime.now(UTC).isoformat()
    }
    if reply_to is not None:
        message["reply_to"] = reply_to
    messages.append(message)


def get_recent_messages(n: int) -> List[dict]:
    """Return the n most recent messages."""
    return messages[-n:]


def save_session(path: str):
    """Save all messages to a JSON file at the given path."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)


def load_session(path: str):
    """Load messages from a JSON file at the given path, replacing the current session."""
    global messages
    with open(path, 'r', encoding='utf-8') as f:
        messages = json.load(f)
