from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Document(Base):
    """Metadata for every uploaded and ingested document."""

    __tablename__ = "documents"

    id: int = Column(Integer, primary_key=True, index=True)
    filename: str = Column(String, nullable=False)
    file_type: str = Column(String, nullable=False)
    chunk_strategy: str = Column(String, nullable=False)
    total_chunks: int = Column(Integer, nullable=False)
    uploaded_at: datetime = Column(DateTime, default=datetime.utcnow)


class Booking(Base):
    """Interview booking records extracted by the LLM."""

    __tablename__ = "bookings"

    id: int = Column(Integer, primary_key=True, index=True)
    session_id: str = Column(String, nullable=False)
    name: str = Column(String, nullable=False)
    email: str = Column(String, nullable=False)
    date: str = Column(String, nullable=False)
    time: str = Column(String, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
