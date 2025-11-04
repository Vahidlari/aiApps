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

import logging
from typing import Any, Dict, List, Optional

from weaviate.classes.query import Filter, MetadataQuery

from .database_manager import DatabaseManager
from .embedding_engine import EmbeddingEngine
from .models import RetrievalMetadata, SearchResultItem


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
        filter: Optional[Filter] = None,
    ) -> List[SearchResultItem]:
        """Search for similar documents using vector similarity.

        This method performs semantic search using vector embeddings to find
        documents that are semantically similar to the query.

        Args:
            query: Search query text
            collection: Collection name to search
            top_k: Number of results to return
            score_threshold: Minimum similarity score threshold
            filter: Optional Weaviate Filter object to filter results

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
                filter=filter,
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
        filter: Optional[Filter] = None,
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
            filter: Optional Weaviate Filter object to filter results by properties

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
                filter=filter,
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
        filter: Optional[Filter] = None,
    ) -> List[SearchResultItem]:
        """Perform keyword search using BM25 algorithm.

        This method performs traditional keyword search using BM25 algorithm
        to find documents containing specific keywords.

        Args:
            query: Search query text
            collection: Collection name to search
            top_k: Number of results to return
            score_threshold: Minimum similarity score threshold
            filter: Optional Weaviate Filter object to filter results by properties

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
                filter=filter,
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
