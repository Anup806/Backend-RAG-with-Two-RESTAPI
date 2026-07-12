import os
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from qdrant_client.http.exceptions import ResponseHandlingException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.crud import save_document_metadata
from app.db.database import get_db
from app.services.chunker import chunk_text
from app.services.embedder import embed_texts
from app.services.extractor import extract_text
from app.services.vector_store import store_chunks

router = APIRouter(prefix="/ingest", tags=["Document Ingestion"])

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS: set[str] = {"pdf", "txt"}
ALLOWED_STRATEGIES: set[str] = {"fixed", "sentence"}


@router.post("/upload", summary="Upload and ingest a document")
async def upload_document(
    file: UploadFile = File(..., description="PDF or TXT file to ingest"),
    strategy: str = Form(
        ..., description="Chunking strategy: 'fixed' (character-based) or 'sentence' (sentence-based)"
    ),
    db: Session = Depends(get_db),
) -> dict:
    """
    Upload a PDF or TXT file and ingest it into the RAG system.

    Steps performed:
    1. Validate file type and chunking strategy
    2. Extract raw text from the file
    3. Split text into chunks using the selected strategy
    4. Generate embeddings for each chunk
    5. Store embeddings in Qdrant vector database
    6. Save document metadata to SQLite

    Returns document ID, filename, strategy used, and chunk count.
    """
    # Validate file extension
    file_ext = file.filename.split(".")[-1].lower() if file.filename else ""
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file_ext}'. Allowed: pdf, txt.",
        )

    # Validate strategy
    if strategy not in ALLOWED_STRATEGIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid strategy '{strategy}'. Use 'fixed' or 'sentence'.",
        )

    # Save file to disk temporarily
    temp_path = UPLOAD_DIR / file.filename
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Extract text
        text: str = extract_text(str(temp_path), file_ext)
        if not text:
            raise HTTPException(
                status_code=422,
                detail="No text could be extracted from the file.",
            )

        # Chunk text
        chunks: list[str] = chunk_text(text, strategy=strategy)
        if not chunks:
            raise HTTPException(
                status_code=422,
                detail="Document produced zero chunks. File may be empty.",
            )

        # Embed all chunks
        embeddings: list[list[float]] = embed_texts(chunks)

        # Persist metadata to SQLite
        doc_record = save_document_metadata(
            db=db,
            filename=file.filename,
            file_type=file_ext,
            chunk_strategy=strategy,
            total_chunks=len(chunks),
        )

        # Store in Qdrant
        try:
            stored_count: int = store_chunks(
                chunks=chunks,
                embeddings=embeddings,
                document_id=doc_record.id,
                filename=file.filename,
            )
        except ResponseHandlingException as exc:
            raise HTTPException(
                status_code=503,
                detail="Qdrant is unavailable. Start the vector database and try again.",
            ) from exc

        return {
            "message": "Document ingested successfully.",
            "document_id": doc_record.id,
            "filename": file.filename,
            "strategy_used": strategy,
            "total_chunks_stored": stored_count,
        }

    finally:
        # Always remove the temp file regardless of success or failure
        if temp_path.exists():
            os.remove(temp_path)
