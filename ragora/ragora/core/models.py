"""Domain models for retrieval results.

This module contains the core data models used for retrieval operations in the
RAG system. These models represent the structured data returned from search
and retrieval operations, providing type-safe access to chunk content,
metadata, and search scores.

Key Models:
- RetrievalMetadata: Structured metadata extracted from stored properties
- RetrievalResultItem: Base class for all chunk retrieval results
- SearchResultItem: Search results with scores (extends RetrievalResultItem)
"""

import json
from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class RetrievalMetadata(BaseModel):
    """Structured metadata for search results.

    Extracts and organizes metadata fields from stored properties,
    providing type-safe access to chunk, document, and email metadata.
    """

    # Chunk metadata
    chunk_idx: Optional[int] = Field(default=None, description="Chunk index")
    chunk_size: Optional[int] = Field(default=None, description="Chunk size")
    total_chunks: Optional[int] = Field(
        default=None, description="Total chunks in document"
    )
    created_at: Optional[str] = Field(default=None, description="Creation timestamp")

    # Document metadata
    source_document: Optional[str] = Field(
        default=None, description="Source document filename"
    )
    page_number: Optional[int] = Field(default=None, description="Page number")
    section_title: Optional[str] = Field(
        default=None, description="Section or chapter title"
    )
    chunk_type: Optional[str] = Field(
        default=None,
        description="Type of chunk (text, citation, equation, etc.)",
    )

    # Email metadata
    email_subject: Optional[str] = Field(default=None, description="Email subject line")
    email_sender: Optional[str] = Field(
        default=None, description="Email sender address"
    )
    email_recipient: Optional[str] = Field(
        default=None, description="Email recipient address"
    )
    email_date: Optional[str] = Field(default=None, description="Email timestamp")
    email_id: Optional[str] = Field(default=None, description="Unique email identifier")
    email_folder: Optional[str] = Field(default=None, description="Email folder/path")

    # Custom metadata
    custom_metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Custom metadata dictionary"
    )
    language: Optional[str] = Field(
        default=None, description="Content language (e.g., en, es, fr)"
    )
    domain: Optional[str] = Field(
        default=None,
        description="Content domain (e.g., scientific, legal, medical)",
    )
    confidence: Optional[float] = Field(
        default=None, description="Processing confidence score (0.0-1.0)"
    )
    tags: Optional[str] = Field(
        default=None, description="Comma-separated tags/categories"
    )
    priority: Optional[int] = Field(
        default=None, description="Content priority/importance level"
    )
    content_category: Optional[str] = Field(
        default=None, description="Fine-grained content categorization"
    )

    @classmethod
    def from_properties(cls, properties: Dict[str, Any]) -> "RetrievalMetadata":
        """Create RetrievalMetadata from properties dictionary.

        Args:
            properties: Dictionary containing stored properties

        Returns:
            RetrievalMetadata instance
        """
        # Parse custom_metadata JSON string if present
        custom_meta = properties.get("custom_metadata")
        if custom_meta:
            if isinstance(custom_meta, str):
                try:
                    custom_meta = json.loads(custom_meta) if custom_meta else None
                except (json.JSONDecodeError, TypeError):
                    custom_meta = None
            elif not isinstance(custom_meta, dict):
                custom_meta = None
        else:
            custom_meta = None

        return cls(
            chunk_idx=properties.get("metadata_chunk_idx"),
            chunk_size=properties.get("metadata_chunk_size"),
            total_chunks=properties.get("metadata_total_chunks"),
            created_at=properties.get("metadata_created_at")
            or properties.get("created_at"),
            source_document=properties.get("source_document"),
            page_number=properties.get("page_number"),
            section_title=properties.get("section_title"),
            chunk_type=properties.get("chunk_type"),
            email_subject=properties.get("email_subject"),
            email_sender=properties.get("email_sender"),
            email_recipient=properties.get("email_recipient"),
            email_date=properties.get("email_date"),
            email_id=properties.get("email_id"),
            email_folder=properties.get("email_folder"),
            custom_metadata=custom_meta,
            language=properties.get("language"),
            domain=properties.get("domain"),
            confidence=properties.get("confidence"),
            tags=properties.get("tags"),
            priority=properties.get("priority"),
            content_category=properties.get("content_category"),
        )


class RetrievalResultItem(BaseModel):
    """Base class for all chunk retrieval results.

    Contains common fields shared by both direct retrieval and search
    results. This base class provides the core chunk data without
    retrieval-specific context.
    """

    # Core content
    content: str = Field(..., description="Text content of the chunk")
    chunk_id: str = Field(..., description="Unique chunk identifier")

    # All stored properties (full dict for backward compatibility)
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="All stored properties from the vector database",
    )

    # Structured metadata
    metadata: RetrievalMetadata = Field(
        default_factory=RetrievalMetadata,
        description="Structured metadata extracted from properties",
    )


class SearchResultItem(RetrievalResultItem):
    """Search result item extending base retrieval result.

    Adds search-specific context: scores, retrieval method, and timestamp.
    This is used for results returned from search operations.
    """

    # Retrieval scores
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Similarity score (0.0-1.0)",
    )
    distance: Optional[float] = Field(
        default=None, description="Distance metric (for vector similarity)"
    )
    hybrid_score: Optional[float] = Field(
        default=None, description="Hybrid search score"
    )
    bm25_score: Optional[float] = Field(
        default=None, description="BM25 keyword search score"
    )

    # Retrieval context
    retrieval_method: Literal[
        "vector_similarity", "hybrid_search", "keyword_search"
    ] = Field(..., description="Method used for retrieval")
    retrieval_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when retrieval occurred",
    )

    # Convenience properties for email results
    @property
    def subject(self) -> Optional[str]:
        """Email subject (if applicable)."""
        return self.properties.get("email_subject") or self.metadata.email_subject

    @property
    def sender(self) -> Optional[str]:
        """Email sender (if applicable)."""
        return self.properties.get("email_sender") or self.metadata.email_sender

    @field_validator("retrieval_timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, v: Any) -> datetime:
        """Parse timestamp from string or datetime.

        Args:
            v: Timestamp value (datetime or ISO format string)

        Returns:
            datetime: Parsed datetime object

        Raises:
            ValueError: If the value cannot be parsed into a valid datetime
        """
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except (ValueError, AttributeError) as e:
                raise ValueError(
                    f"Invalid timestamp string format: {v}. "
                    f"Expected ISO 8601 format (e.g., '2024-01-15T14:30:00Z')."
                ) from e
        if v is None:
            raise ValueError(
                "retrieval_timestamp cannot be None. "
                "If not provided, it will default to the current time."
            )
        raise ValueError(
            f"Invalid timestamp type: {type(v).__name__}. "
            f"Expected datetime or ISO 8601 format string."
        )
