import nltk

# Download sentence tokenizer data on first import
try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab", quiet=True)


def fixed_size_chunk(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[str]:
    """
    Split text into fixed-size character chunks with sliding overlap.

    Example with chunk_size=20, overlap=5:
        "The quick brown fox jumps..."
        → ["The quick brown fox ", "fox jumps over the ", ...]

    Args:
        text: Raw text to split.
        chunk_size: Number of characters per chunk.
        overlap: Number of characters to repeat between consecutive chunks.

    Returns:
        List of non-empty text chunks.
    """
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def sentence_based_chunk(
    text: str,
    sentences_per_chunk: int = 5,
) -> list[str]:
    """
    Split text by sentences, grouping N sentences per chunk.

    Preserves semantic boundaries — avoids cutting mid-sentence.

    Args:
        text: Raw text to split.
        sentences_per_chunk: How many sentences to group into one chunk.

    Returns:
        List of non-empty text chunks.
    """
    sentences: list[str] = nltk.sent_tokenize(text)
    chunks: list[str] = []
    for i in range(0, len(sentences), sentences_per_chunk):
        group = " ".join(sentences[i : i + sentences_per_chunk]).strip()
        if group:
            chunks.append(group)
    return chunks


def chunk_text(
    text: str,
    strategy: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[str]:
    """
    Route to the correct chunking strategy by name.

    Args:
        text: Raw document text.
        strategy: 'fixed' or 'sentence'.
        chunk_size: Used only for 'fixed' strategy.
        overlap: Used only for 'fixed' strategy.

    Returns:
        List of text chunks.

    Raises:
        ValueError: If strategy is not 'fixed' or 'sentence'.
    """
    if strategy == "fixed":
        return fixed_size_chunk(text, chunk_size, overlap)
    elif strategy == "sentence":
        return sentence_based_chunk(text)
    else:
        raise ValueError(
            f"Unknown chunking strategy: '{strategy}'. Use 'fixed' or 'sentence'."
        )
