import json

import redis

from app.core.config import settings

# Lazy-loaded Redis client singleton
_redis: redis.Redis | None = None

# TTL for chat sessions: 24 hours
SESSION_TTL_SECONDS = 86_400


def _get_redis() -> redis.Redis:
    """Return a shared Redis client instance."""
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


def _session_key(session_id: str) -> str:
    """Build the Redis key for a given session."""
    return f"chat:{session_id}"


def get_chat_history(session_id: str) -> list[dict[str, str]]:
    """
    Retrieve the full conversation history for a session.

    Args:
        session_id: Unique identifier for the conversation.

    Returns:
        List of message dicts with keys 'role' and 'content'.
        Returns an empty list if the session does not exist.
    """
    raw = _get_redis().get(_session_key(session_id))
    return json.loads(raw) if raw else []


def save_chat_history(
    session_id: str,
    history: list[dict[str, str]],
) -> None:
    """
    Persist the entire conversation history back to Redis.

    Args:
        session_id: Unique identifier for the conversation.
        history: Full list of message dicts to save.
    """
    _get_redis().set(
        _session_key(session_id),
        json.dumps(history),
        ex=SESSION_TTL_SECONDS,
    )


def append_to_history(
    session_id: str,
    user_message: str,
    assistant_response: str,
) -> None:
    """
    Append one user+assistant turn to the conversation history.

    Args:
        session_id: Unique identifier for the conversation.
        user_message: The user's raw message text.
        assistant_response: The assistant's response text.
    """
    history = get_chat_history(session_id)
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": assistant_response})
    save_chat_history(session_id, history)


def clear_history(session_id: str) -> None:
    """
    Delete all conversation history for a session.

    Args:
        session_id: Unique identifier for the conversation.
    """
    _get_redis().delete(_session_key(session_id))
