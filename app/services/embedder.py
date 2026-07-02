from sentence_transformers import SentenceTransformer

from app.core.config import settings

# Lazy-loaded singleton — model loads on first call, not at import time
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Load the embedding model once and reuse it for the process lifetime."""
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a batch of text strings.

    Args:
        texts: List of strings to embed.

    Returns:
        List of embedding vectors (each a list of floats).
    """
    model = _get_model()
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings.tolist()


def embed_query(query: str) -> list[float]:
    """
    Generate an embedding for a single query string.

    Args:
        query: The user's search query.

    Returns:
        Embedding vector as a list of floats.
    """
    return embed_texts([query])[0]
