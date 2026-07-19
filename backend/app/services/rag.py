from groq import Groq

from app.core.config import settings
from app.services.embedder import embed_query
from app.services.memory import get_chat_history
from app.services.vector_store import search_similar

_groq_client: Groq | None = None

_RAG_SYSTEM_PROMPT = """You are a helpful assistant. Answer ONLY using the context provided below.
If the answer is not found in the context, say exactly:
"I don't have information about that in the uploaded documents."
Never make up information. Be concise and factual."""

# Exact fallback string the model is instructed to use above. Checked verbatim
# so we don't attach citations to an answer that wasn't actually grounded.
_NO_INFO_ANSWER = "I don't have information about that in the uploaded documents."

# Max history turns to include in the prompt (each turn = 1 user + 1 assistant message)
_MAX_HISTORY_TURNS = 3

# How much of a chunk's text to surface as a citation preview
_SNIPPET_MAX_CHARS = 160


def _make_snippet(text: str, max_chars: int = _SNIPPET_MAX_CHARS) -> str:
    """Trim a chunk's text to a short, UI-friendly preview."""
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[:max_chars].rsplit(" ", 1)[0] + "…"


def _get_groq() -> Groq:
    """Return a shared Groq client instance."""
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
    return _groq_client


def _build_messages(
    user_query: str,
    context_chunks: list[dict],
    chat_history: list[dict[str, str]],
) -> list[dict[str, str]]:
    """
    Assemble the full message list for the LLM:
    system prompt + context → trimmed history → current user query.

    Args:
        user_query: The user's current message.
        context_chunks: Retrieved chunks from Qdrant.
        chat_history: Full Redis conversation history.

    Returns:
        List of message dicts ready for the Groq API.
    """
    context_text = "\n\n".join(
        f"[Source: {c['filename']}]\n{c['text']}" for c in context_chunks
    )

    system_content = f"{_RAG_SYSTEM_PROMPT}\n\nContext:\n{context_text}"

    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_content}
    ]

    # Include only the last N turns to avoid exceeding token limits
    recent_history = chat_history[-(_MAX_HISTORY_TURNS * 2):]
    messages.extend(recent_history)

    messages.append({"role": "user", "content": user_query})

    return messages


def generate_rag_response(
    user_query: str,
    session_id: str,
) -> dict:
    """
    Execute the full custom RAG pipeline manually (no RetrievalQAChain).

    Pipeline steps:
        1. Embed the user query with sentence-transformers
        2. Search Qdrant for the top-k most relevant chunks
        3. Load conversation history from Redis
        4. Build a prompt: system + context + history + query
        5. Call the Groq LLM
        6. Return the answer with source filenames

    Args:
        user_query: The user's current question.
        session_id: Redis session key for conversation history.

    Returns:
        Dict with keys: answer (str), sources (list[str]), chunks_used (int).
    """
    # Step 1 — Embed query
    query_vector: list[float] = embed_query(user_query)

    # Step 2 — Retrieve relevant chunks from Qdrant
    context_chunks: list[dict] = search_similar(
        query_embedding=query_vector,
        top_k=settings.TOP_K,
    )

    # Step 3 — Load Redis chat history
    chat_history: list[dict[str, str]] = get_chat_history(session_id)

    # Step 4 — Build prompt
    messages = _build_messages(user_query, context_chunks, chat_history)

    # Step 5 — Call LLM
    client = _get_groq()
    completion = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=messages,
        temperature=0.2,
        max_tokens=1000,
    )

    answer: str = completion.choices[0].message.content.strip()

    # Step 6 — Build structured citations, one entry per source file, keeping
    # that file's highest-scoring chunk as the preview snippet. Skipped
    # entirely for the "no info" fallback: those chunks were retrieved but
    # not actually used to ground an answer, so citing them would be
    # misleading (it would look like the answer came from those documents
    # when the model explicitly said it couldn't answer).
    sources: list[dict] = []
    if answer != _NO_INFO_ANSWER:
        best_by_file: dict[str, dict] = {}
        for chunk in context_chunks:
            filename = chunk["filename"]
            if filename not in best_by_file or chunk["score"] > best_by_file[filename]["score"]:
                best_by_file[filename] = chunk

        sources = [
            {
                "filename": filename,
                "snippet": _make_snippet(chunk["text"]),
                "score": round(chunk["score"], 3),
            }
            for filename, chunk in sorted(
                best_by_file.items(), key=lambda kv: kv[1]["score"], reverse=True
            )
        ]

    return {
        "answer": answer,
        "sources": sources,
        "chunks_used": len(context_chunks),
    }