"""Retrieval system for RAG implementation.

This module provides the Retriever class that handles search and
retrieval operations for the RAG system. It separates search logic from
storage operations,
following the single responsibility principle.

Key responsibilities:
- Vector similarity search
- Hybrid search (vector + keyword)
- Query preprocessing and optimization
- Result ranking and filtering
- Query expansion and normalization

The retriever uses the VectorStore for data access but handles all search
logic independently, enabling better testability and maintainability.
"""

import logging
from typing import Any, Dict, List, Optional

from .embedding_engine import EmbeddingEngine
from .vector_store import VectorStore


class Retriever:
    """Retrieval system for document search and retrieval.

    This class handles all search and retrieval operations, separating
    search logic from storage concerns. It uses VectorStore for data access
    but implements its own search algorithms and query processing.

    Attributes:
        vector_store: VectorStore instance for data access
        embedding_engine: EmbeddingEngine for query embeddings
        logger: Logger instance for debugging and monitoring
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_engine: Optional[EmbeddingEngine] = None,
    ):
        """Initialize the Retriever.

        Args:
            vector_store: VectorStore instance for data access
            embedding_engine: EmbeddingEngine instance (optional, will use
                the one from vector_store if not provided)

        Raises:
            ValueError: If vector_store is None
        """
        if vector_store is None:
            raise ValueError("VectorStore cannot be None")

        self.vector_store = vector_store
        self.embedding_engine = embedding_engine or vector_store.embedding_engine
        self.logger = logging.getLogger(__name__)

    def search_similar(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar documents using vector similarity.

        This method performs semantic search using vector embeddings to find
        documents that are semantically similar to the query.

        Args:
            query: Search query text
            top_k: Number of results to return
            score_threshold: Minimum similarity score threshold
            filters: Optional filters to apply to the search

        Returns:
            List[Dict[str, Any]]: List of search results with metadata

        Raises:
            ValueError: If query is empty
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            self.logger.debug(f"Performing vector similarity search: '{query}'")

            # Preprocess query for better results
            processed_query = self._preprocess_query(query)

            # Perform search using vector store
            results = self.vector_store._search_similar_internal(
                query=processed_query,
                top_k=top_k,
                score_threshold=score_threshold,
                filters=filters,
            )

            # Post-process results
            processed_results = self._postprocess_results(results)

            self.logger.debug(
                f"Found {len(processed_results)} similar results for: " f"'{query}'"
            )
            return processed_results

        except Exception as e:
            self.logger.error(f"Vector similarity search failed: {str(e)}")
            raise

    def search_hybrid(
        self,
        query: str,
        top_k: int = 5,
        alpha: float = 0.5,
        score_threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search combining vector and keyword search.

        This method combines semantic similarity search with traditional
        keyword
        search to provide more comprehensive results.

        Args:
            query: Search query text
            top_k: Number of results to return
            alpha: Weight for vector search (0.0 = keyword only,
                1.0 = vector only)
            score_threshold: Minimum similarity score threshold
            filters: Optional filters to apply to the search

        Returns:
            List[Dict[str, Any]]: List of search results with metadata

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

            # Perform hybrid search using vector store
            results = self.vector_store._search_hybrid_internal(
                query=processed_query,
                top_k=top_k,
                alpha=alpha,
                score_threshold=score_threshold,
                filters=filters,
            )

            # Post-process results
            processed_results = self._postprocess_results(results)

            self.logger.debug(
                f"Found {len(processed_results)} hybrid results for: " f"'{query}'"
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

    def _postprocess_results(
        self, results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Post-process search results for better presentation.

        Args:
            results: Raw search results

        Returns:
            List[Dict[str, Any]]: Processed results
        """
        # Sort by similarity score (highest first)
        results.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)

        # Add additional metadata
        for result in results:
            result["retrieval_method"] = "vector_similarity"
            result["retrieval_timestamp"] = self._get_current_timestamp()

        return results

    def _get_current_timestamp(self) -> str:
        """Get current timestamp for result metadata.

        Returns:
            str: Current timestamp
        """
        from datetime import datetime

        return datetime.now().isoformat()

    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval system statistics.

        Returns:
            Dict[str, Any]: Retrieval statistics
        """
        try:
            # Get vector store stats
            vector_stats = self.vector_store.get_stats()

            # Add retrieval-specific stats
            retrieval_stats = {
                "vector_store_stats": vector_stats,
                "embedding_model": self.embedding_engine.model_name,
                "embedding_dimension": (self.embedding_engine.embedding_dimension),
                "retrieval_methods": [
                    "vector_similarity",
                    "hybrid_search",
                ],
            }

            return retrieval_stats

        except Exception as e:
            self.logger.error(f"Failed to get retrieval stats: {str(e)}")
            raise
