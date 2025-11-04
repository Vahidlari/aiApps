"""Retrieval system for RAG implementation.

This module provides the Retriever class that handles search and
retrieval operations for the RAG system. It separates search logic from
storage operations, following the single responsibility principle.

Key responsibilities:
- Vector similarity search using Weaviate APIs
- Hybrid search (vector + keyword) using Weaviate APIs
- Keyword search (BM25) using Weaviate APIs
- Query preprocessing and optimization
- Result ranking and filtering
- Query expansion and normalization

The retriever uses DatabaseManager for data access but handles all search
logic independently, enabling better testability and maintainability.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator
from weaviate.classes.query import MetadataQuery

from .database_manager import DatabaseManager
from .embedding_engine import EmbeddingEngine


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
        """Parse timestamp from string or datetime."""
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                return datetime.now()
        return datetime.now()


class Retriever:
    """Retrieval system for document search and retrieval.

    This class handles all search and retrieval operations, separating
    search logic from storage concerns. It uses DatabaseManager for data access
    but implements its own search algorithms and query processing.

    Attributes:
        db_manager: DatabaseManager instance for database access
        class_name: Name of the collection to search
        embedding_engine: EmbeddingEngine for query embeddings
        logger: Logger instance for debugging and monitoring
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        embedding_engine: Optional[EmbeddingEngine] = None,
    ):
        """Initialize the Retriever.

        Args:
            db_manager: DatabaseManager instance for database access
            embedding_engine: EmbeddingEngine instance (optional, defaults to None)

        Raises:
            ValueError: If db_manager is None
        """
        if db_manager is None:
            raise ValueError("DatabaseManager cannot be None")

        self.db_manager = db_manager

        # Note: Embedding engine is not needed when using Weaviate's
        # text2vec-transformers. Weaviate handles embeddings server-side.
        # EmbeddingEngine is only kept for potential future use cases where
        # client-side embeddings might be needed. DO NOT initialize it by
        # default to avoid unnecessary model loading.
        self.embedding_engine = embedding_engine

        self.logger = logging.getLogger(__name__)

    def search_similar(
        self,
        query: str,
        collection: str,
        top_k: int = 5,
        score_threshold: float = 0.0,
    ) -> List[SearchResultItem]:
        """Search for similar documents using vector similarity.

        This method performs semantic search using vector embeddings to find
        documents that are semantically similar to the query.

        Args:
            query: Search query text
            collection: Collection name to search
            top_k: Number of results to return
            score_threshold: Minimum similarity score threshold

        Returns:
            List[SearchResultItem]: List of search result items

        Raises:
            ValueError: If query is empty
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            self.logger.debug(f"Performing vector similarity search: '{query}'")

            # Preprocess query for better results
            processed_query = self._preprocess_query(query)

            # Get collection and execute search using Weaviate APIs
            collection = self.db_manager.get_collection(collection)

            # Use Weaviate's native near_text API
            result = collection.query.near_text(
                query=processed_query,
                limit=top_k,
                return_metadata=MetadataQuery(distance=True),
            )

            # Process results
            processed_results = self._process_vector_results(
                result.objects, score_threshold
            )

            self.logger.debug(
                f"Found {len(processed_results)} similar results for: '{query}'"
            )
            return processed_results

        except Exception as e:
            self.logger.error(f"Vector similarity search failed: {str(e)}")
            raise

    def search_hybrid(
        self,
        query: str,
        collection: str,
        top_k: int = 5,
        alpha: float = 0.5,
        score_threshold: float = 0.0,
    ) -> List[SearchResultItem]:
        """Perform hybrid search combining vector and keyword search.

        This method combines semantic similarity search with traditional
        keyword search to provide more comprehensive results.

        Args:
            query: Search query text
            collection: Collection name to search
            top_k: Number of results to return
            alpha: Weight for vector search (0.0 = keyword only,
                1.0 = vector only)
            score_threshold: Minimum similarity score threshold

        Returns:
            List[SearchResultItem]: List of search result items

        Raises:
            ValueError: If query is empty or alpha is out of range
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if not 0.0 <= alpha <= 1.0:
            raise ValueError("Alpha must be between 0.0 and 1.0")

        try:
            self.logger.debug(f"Performing hybrid search: '{query}' with alpha={alpha}")

            # Preprocess query for better results
            processed_query = self._preprocess_query(query)

            # Get collection and execute hybrid search using Weaviate APIs
            collection = self.db_manager.get_collection(collection)

            # Use Weaviate's native hybrid API
            result = collection.query.hybrid(
                query=processed_query,
                alpha=alpha,
                limit=top_k,
                return_metadata=MetadataQuery(score=True),
            )

            # Process results
            processed_results = self._process_hybrid_results(
                result.objects, score_threshold
            )

            self.logger.debug(
                f"Found {len(processed_results)} hybrid results for: '{query}'"
            )
            return processed_results

        except Exception as e:
            self.logger.error(f"Hybrid search failed: {str(e)}")
            raise

    def _preprocess_query(self, query: str) -> str:
        """Preprocess query for better search results.

        Args:
            query: Original query text

        Returns:
            str: Preprocessed query text
        """
        # Basic preprocessing - normalize whitespace and case
        import re

        processed = re.sub(r"\s+", " ", query.strip())
        processed = processed.lower()

        return processed

    def search_keyword(
        self,
        query: str,
        collection: str,
        top_k: int = 5,
        score_threshold: float = 0.0,
    ) -> List[SearchResultItem]:
        """Perform keyword search using BM25 algorithm.

        This method performs traditional keyword search using BM25 algorithm
        to find documents containing specific keywords.

        Args:
            query: Search query text
            collection: Collection name to search
            top_k: Number of results to return
            score_threshold: Minimum similarity score threshold

        Returns:
            List[SearchResultItem]: List of search result items

        Raises:
            ValueError: If query is empty
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            self.logger.debug(f"Performing keyword search: '{query}'")

            # Preprocess query for better results
            processed_query = self._preprocess_query(query)

            # Get collection and execute keyword search using Weaviate APIs
            collection = self.db_manager.get_collection(collection)

            # Use Weaviate's native BM25 API
            result = collection.query.bm25(
                query=processed_query,
                limit=top_k,
                return_metadata=MetadataQuery(score=True),
            )

            # Process results
            processed_results = self._process_keyword_results(
                result.objects, score_threshold
            )

            self.logger.debug(
                f"Found {len(processed_results)} keyword results for: '{query}'"
            )
            return processed_results

        except Exception as e:
            self.logger.error(f"Keyword search failed: {str(e)}")
            raise

    def _process_vector_results(
        self, objects: List[Any], score_threshold: float
    ) -> List[SearchResultItem]:
        """Process vector search results from Weaviate.

        Args:
            objects: Raw Weaviate objects
            score_threshold: Minimum score threshold

        Returns:
            List[SearchResultItem]: Processed results
        """
        results = []
        for obj in objects:
            # Calculate similarity score from distance
            distance = (
                obj.metadata.distance if obj.metadata and obj.metadata.distance else 1.0
            )
            similarity_score = 1.0 - distance

            if similarity_score >= score_threshold:
                # Build a consistent result that includes all stored properties
                properties = dict(obj.properties or {})

                # Create RetrievalMetadata from properties
                metadata = RetrievalMetadata.from_properties(properties)

                # Build SearchResultItem
                result = SearchResultItem(
                    content=properties.get("content", ""),
                    chunk_id=properties.get("chunk_id", ""),
                    properties=properties,
                    similarity_score=similarity_score,
                    distance=distance,
                    retrieval_method="vector_similarity",
                    retrieval_timestamp=self._get_current_timestamp(),
                    metadata=metadata,
                )
                results.append(result)

        # Sort by similarity score (highest first)
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results

    def _process_hybrid_results(
        self, objects: List[Any], score_threshold: float
    ) -> List[SearchResultItem]:
        """Process hybrid search results from Weaviate.

        Args:
            objects: Raw Weaviate objects
            score_threshold: Minimum score threshold

        Returns:
            List[SearchResultItem]: Processed results
        """
        results = []
        for obj in objects:
            # Get hybrid score
            hybrid_score = (
                obj.metadata.score if obj.metadata and obj.metadata.score else 0.0
            )

            if hybrid_score >= score_threshold:
                # Build a consistent result that includes all stored properties
                properties = dict(obj.properties or {})

                # Create RetrievalMetadata from properties
                metadata = RetrievalMetadata.from_properties(properties)

                # Build SearchResultItem
                result = SearchResultItem(
                    content=properties.get("content", ""),
                    chunk_id=properties.get("chunk_id", ""),
                    properties=properties,
                    similarity_score=hybrid_score,
                    hybrid_score=hybrid_score,
                    retrieval_method="hybrid_search",
                    retrieval_timestamp=self._get_current_timestamp(),
                    metadata=metadata,
                )
                results.append(result)

        # Sort by hybrid score (highest first)
        results.sort(key=lambda x: x.hybrid_score or 0.0, reverse=True)
        return results

    def _process_keyword_results(
        self, objects: List[Any], score_threshold: float
    ) -> List[SearchResultItem]:
        """Process keyword search results from Weaviate.

        Args:
            objects: Raw Weaviate objects
            score_threshold: Minimum score threshold

        Returns:
            List[SearchResultItem]: Processed results
        """
        results = []
        for obj in objects:
            # Get BM25 score
            bm25_score = (
                obj.metadata.score if obj.metadata and obj.metadata.score else 0.0
            )

            if bm25_score >= score_threshold:
                # Build a consistent result that includes all stored properties
                properties = dict(obj.properties or {})

                # Create RetrievalMetadata from properties
                metadata = RetrievalMetadata.from_properties(properties)

                # Build SearchResultItem
                result = SearchResultItem(
                    content=properties.get("content", ""),
                    chunk_id=properties.get("chunk_id", ""),
                    properties=properties,
                    similarity_score=bm25_score,
                    bm25_score=bm25_score,
                    retrieval_method="keyword_search",
                    retrieval_timestamp=self._get_current_timestamp(),
                    metadata=metadata,
                )
                results.append(result)

        # Sort by BM25 score (highest first)
        results.sort(key=lambda x: x.bm25_score or 0.0, reverse=True)
        return results

    def _get_current_timestamp(self) -> str:
        """Get current timestamp for result metadata.

        Returns:
            str: Current timestamp
        """
        from datetime import datetime

        return datetime.now().isoformat()

    def get_retrieval_stats(self, collection: str) -> Dict[str, Any]:
        """Get retrieval system statistics.

        Returns:
            Dict[str, Any]: Retrieval statistics
        """
        try:
            # Get database manager stats
            db_stats = {
                "is_connected": self.db_manager.is_connected,
                "url": self.db_manager.url,
                "collections": self.db_manager.list_collections(),
            }

            # Add retrieval-specific stats
            embedding_info = (
                {
                    "embedding_model": self.embedding_engine.model_name,
                    "embedding_dimension": (self.embedding_engine.embedding_dimension),
                }
                if self.embedding_engine
                else {
                    "embedding_model": ("Weaviate text2vec-transformers (server-side)"),
                    "embedding_dimension": "N/A (server-side)",
                }
            )

            retrieval_stats = {
                "database_stats": db_stats,
                "collection": collection,
                **embedding_info,
                "retrieval_methods": [
                    "vector_similarity",
                    "hybrid_search",
                    "keyword_search",
                ],
            }

            return retrieval_stats

        except Exception as e:
            self.logger.error(f"Failed to get retrieval stats: {str(e)}")
            raise
