import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import settings

# Lazy-loaded singleton Qdrant client
_client: QdrantClient | None = None


def _get_client() -> QdrantClient:
    """Return a shared Qdrant client instance."""
    global _client
    if _client is None:
        _client = QdrantClient(url=settings.QDRANT_URL)
    return _client


def ensure_collection(vector_size: int = 384) -> None:
    """
    Create the Qdrant collection if it does not already exist.

    Args:
        vector_size: Dimensionality of the embedding vectors.
                     all-MiniLM-L6-v2 produces 384-dim vectors.
    """
    client = _get_client()
    existing_names = [c.name for c in client.get_collections().collections]
    if settings.QDRANT_COLLECTION not in existing_names:
        client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )


def store_chunks(
    chunks: list[str],
    embeddings: list[list[float]],
    document_id: int,
    filename: str,
) -> int:
    """
    Upsert text chunks and their embeddings into Qdrant.

    Args:
        chunks: List of text strings (one per chunk).
        embeddings: Corresponding embedding vectors.
        document_id: SQLite document ID for traceability.
        filename: Original filename for display in search results.

    Returns:
        Number of points stored.
    """
    client = _get_client()
    ensure_collection(vector_size=len(embeddings[0]))

    points: list[PointStruct] = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "text": chunk,
                "document_id": document_id,
                "filename": filename,
            },
        )
        for chunk, embedding in zip(chunks, embeddings)
    ]

    client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)
    return len(points)


def search_similar(
    query_embedding: list[float],
    top_k: int = 5,
) -> list[dict]:
    """
    Find the most semantically similar chunks to a query vector.

    Args:
        query_embedding: Embedding of the user's query.
        top_k: Number of top results to return.

    Returns:
        List of dicts with keys: text, score, filename.
    """
    client = _get_client()
    results = client.search(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=query_embedding,
        limit=top_k,
    )
    return [
        {
            "text": hit.payload["text"],
            "score": hit.score,
            "filename": hit.payload.get("filename", "unknown"),
        }
        for hit in results
    ]
