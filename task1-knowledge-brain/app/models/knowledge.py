from datetime import datetime, timezone
from typing import List, Optional, Any
from sqlalchemy import (
    String, Text, Boolean, Integer, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON
from .base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    url: Mapped[str] = mapped_column(String(1024), unique=True, index=True)
    canonical_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    title: Mapped[str] = mapped_column(String(512), index=True)
    content: Mapped[str] = mapped_column(Text)
    html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    headings: Mapped[List[dict]] = mapped_column(JSON, default=list)
    tables: Mapped[List[dict]] = mapped_column(JSON, default=list)
    category: Mapped[Optional[str]] = mapped_column(String(256), nullable=True, index=True)
    folder: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    chunks: Mapped[List["Chunk"]] = relationship("Chunk", back_populates="article", cascade="all, delete-orphan")
    screenshots: Mapped[List["Screenshot"]] = relationship("Screenshot", back_populates="article", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    article_id: Mapped[str] = mapped_column(String(64), ForeignKey("articles.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    heading_path: Mapped[str] = mapped_column(String(512), default="")
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    embedding_json: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    article: Mapped["Article"] = relationship("Article", back_populates="chunks")


class Screenshot(Base):
    __tablename__ = "screenshots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    article_id: Mapped[str] = mapped_column(String(64), ForeignKey("articles.id", ondelete="CASCADE"), index=True)
    url: Mapped[str] = mapped_column(String(1024))
    local_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    surrounding_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[str] = mapped_column(Text)
    detected_labels: Mapped[List[str]] = mapped_column(JSON, default=list)
    is_legible: Mapped[bool] = mapped_column(Boolean, default=True)
    uncertainty_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    article: Mapped["Article"] = relationship("Article", back_populates="screenshots")


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="running")
    total_discovered: Mapped[int] = mapped_column(Integer, default=0)
    added_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_count: Mapped[int] = mapped_column(Integer, default=0)
    unchanged_count: Mapped[int] = mapped_column(Integer, default=0)
    removed_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)


class IngestionManifest(Base):
    __tablename__ = "ingestion_manifest"

    url: Mapped[str] = mapped_column(String(1024), primary_key=True)
    article_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    etag: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    last_modified: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_crawled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Escalation(Base):
    __tablename__ = "escalations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    question: Mapped[str] = mapped_column(Text)
    context: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    retrieval_results: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)
    reason: Mapped[str] = mapped_column(String(256))
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending, resolved, rejected
    expert_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    supporting_evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
