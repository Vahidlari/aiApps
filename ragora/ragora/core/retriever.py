"""Search utilities that power Ragora retrieval workflows.

The :class:`Retriever` encapsulates vector, keyword, and hybrid search strategies
while delegating persistence to :class:`~ragora.core.database_manager.DatabaseManager`.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from weaviate.classes.query import Filter, MetadataQuery

from .database_manager import DatabaseManager
from .embedding_engine import EmbeddingEngine
from .models import RetrievalMetadata, SearchResultItem


class Retriever:
    """Encapsulates reusable retrieval strategies for Ragora.

    Attributes:
        db_manager: Database access layer.
        embedding_engine: Optional embedding provider for custom workflows.
        logger: Logger used for diagnostic output.

    Examples:
        ```python
        from ragora.core.database_manager import DatabaseManager
        from ragora.core.retriever import Retriever

        db = DatabaseManager(url="http://localhost:8080")
        retriever = Retriever(db_manager=db)
        hits = retriever.search_similar("neural networks", collection="Document")
        ```
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        embedding_engine: Optional[EmbeddingEngine] = None,
    ):
        """Initialize the Retriever.

        Args:
            db_manager: DatabaseManager instance for database access
            embedding_engine: EmbeddingEngine instance
                (optional, defaults to None)

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

        Examples:
            ```python
            hits = retriever.search_similar("rag pipeline", "Document", top_k=10)
            ```
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
                filters=filter,
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
            filter: Optional Weaviate Filter object to filter results
                by properties

        Returns:
            List[SearchResultItem]: List of search result items

        Raises:
            ValueError: If query is empty or alpha is out of range

        Examples:
            ```python
            hits = retriever.search_hybrid(
                "retrieval strategies",
                collection="Document",
                alpha=0.7,
            )
            ```
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
                filters=filter,
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
            filter: Optional Weaviate Filter object to filter results
                by properties

        Returns:
            List[SearchResultItem]: List of search result items

        Raises:
            ValueError: If query is empty

        Examples:
            ```python
            hits = retriever.search_keyword("BM25 overview", "Document", top_k=3)
            ```
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
                filters=filter,
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

    def batch_search_similar(
        self,
        queries: List[str],
        collection: str,
        top_k: int = 5,
        score_threshold: float = 0.0,
        filter: Optional[Filter] = None,
        max_workers: Optional[int] = None,
    ) -> List[List[SearchResultItem]]:
        """Perform batch vector similarity search for multiple queries.

        This method performs semantic search using vector embeddings for multiple
        queries in parallel, improving performance for bulk operations.

        Args:
            queries: List of search query texts
            collection: Collection name to search
            top_k: Number of results to return per query
            score_threshold: Minimum similarity score threshold
            filter: Optional Weaviate Filter object to filter results
            max_workers: Maximum number of parallel workers (default: min(32, len(queries) + 4))

        Returns:
            List[List[SearchResultItem]]: List of search result lists, where each inner list
                corresponds to the query at the same index in the input queries list

        Raises:
            ValueError: If queries list is empty or contains empty strings

        Examples:
            ```python
            queries = ["neural networks", "machine learning", "deep learning"]
            results = retriever.batch_search_similar(queries, "Document", top_k=10)
            # results[0] contains results for "neural networks"
            # results[1] contains results for "machine learning"
            # results[2] contains results for "deep learning"
            ```
        """
        if not queries:
            raise ValueError("Queries list cannot be empty")

        # Validate all queries are non-empty
        for i, query in enumerate(queries):
            if not query or not query.strip():
                raise ValueError(f"Query at index {i} cannot be empty")

        # Determine number of workers
        if max_workers is None:
            max_workers = min(32, len(queries) + 4)

        try:
            self.logger.info(
                f"Performing batch vector similarity search for {len(queries)} queries"
            )

            # Create results list with same length as queries to maintain index alignment
            results: List[List[SearchResultItem]] = [[] for _ in queries]

            # Execute queries in parallel
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all queries
                future_to_index = {
                    executor.submit(
                        self.search_similar,
                        query,
                        collection,
                        top_k,
                        score_threshold,
                        filter,
                    ): i
                    for i, query in enumerate(queries)
                }

                # Collect results as they complete
                for future in as_completed(future_to_index):
                    index = future_to_index[future]
                    try:
                        query_results = future.result()
                        results[index] = query_results
                        self.logger.debug(
                            f"Query {index} ('{queries[index]}') returned {len(query_results)} results"
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Query {index} ('{queries[index]}') failed: {str(e)}"
                        )
                        # Keep empty list for failed query to maintain index alignment
                        results[index] = []

            self.logger.info(
                f"Batch search completed: {len(queries)} queries processed, "
                f"{sum(len(r) for r in results)} total results"
            )
            return results

        except Exception as e:
            self.logger.error(f"Batch vector similarity search failed: {str(e)}")
            raise

    def batch_search_hybrid(
        self,
        queries: List[str],
        collection: str,
        top_k: int = 5,
        alpha: float = 0.5,
        score_threshold: float = 0.0,
        filter: Optional[Filter] = None,
        max_workers: Optional[int] = None,
    ) -> List[List[SearchResultItem]]:
        """Perform batch hybrid search for multiple queries.

        This method combines semantic similarity search with traditional keyword
        search for multiple queries in parallel, improving performance for bulk operations.

        Args:
            queries: List of search query texts
            collection: Collection name to search
            top_k: Number of results to return per query
            alpha: Weight for vector search (0.0 = keyword only, 1.0 = vector only)
            score_threshold: Minimum similarity score threshold
            filter: Optional Weaviate Filter object to filter results by properties
            max_workers: Maximum number of parallel workers (default: min(32, len(queries) + 4))

        Returns:
            List[List[SearchResultItem]]: List of search result lists, where each inner list
                corresponds to the query at the same index in the input queries list

        Raises:
            ValueError: If queries list is empty, contains empty strings, or alpha is out of range

        Examples:
            ```python
            queries = ["retrieval strategies", "vector search", "keyword matching"]
            results = retriever.batch_search_hybrid(
                queries, "Document", alpha=0.7, top_k=10
            )
            # results[0] contains results for "retrieval strategies"
            # results[1] contains results for "vector search"
            # results[2] contains results for "keyword matching"
            ```
        """
        if not queries:
            raise ValueError("Queries list cannot be empty")

        # Validate all queries are non-empty
        for i, query in enumerate(queries):
            if not query or not query.strip():
                raise ValueError(f"Query at index {i} cannot be empty")

        if not 0.0 <= alpha <= 1.0:
            raise ValueError("Alpha must be between 0.0 and 1.0")

        # Determine number of workers
        if max_workers is None:
            max_workers = min(32, len(queries) + 4)

        try:
            self.logger.info(
                f"Performing batch hybrid search for {len(queries)} queries with alpha={alpha}"
            )

            # Create results list with same length as queries to maintain index alignment
            results: List[List[SearchResultItem]] = [[] for _ in queries]

            # Execute queries in parallel
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all queries
                future_to_index = {
                    executor.submit(
                        self.search_hybrid,
                        query,
                        collection,
                        top_k,
                        alpha,
                        score_threshold,
                        filter,
                    ): i
                    for i, query in enumerate(queries)
                }

                # Collect results as they complete
                for future in as_completed(future_to_index):
                    index = future_to_index[future]
                    try:
                        query_results = future.result()
                        results[index] = query_results
                        self.logger.debug(
                            f"Query {index} ('{queries[index]}') returned {len(query_results)} results"
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Query {index} ('{queries[index]}') failed: {str(e)}"
                        )
                        # Keep empty list for failed query to maintain index alignment
                        results[index] = []

            self.logger.info(
                f"Batch search completed: {len(queries)} queries processed, "
                f"{sum(len(r) for r in results)} total results"
            )
            return results

        except Exception as e:
            self.logger.error(f"Batch hybrid search failed: {str(e)}")
            raise

    def batch_search_keyword(
        self,
        queries: List[str],
        collection: str,
        top_k: int = 5,
        score_threshold: float = 0.0,
        filter: Optional[Filter] = None,
        max_workers: Optional[int] = None,
    ) -> List[List[SearchResultItem]]:
        """Perform batch keyword search for multiple queries.

        This method performs traditional keyword search using BM25 algorithm for
        multiple queries in parallel, improving performance for bulk operations.

        Args:
            queries: List of search query texts
            collection: Collection name to search
            top_k: Number of results to return per query
            score_threshold: Minimum similarity score threshold
            filter: Optional Weaviate Filter object to filter results by properties
            max_workers: Maximum number of parallel workers (default: min(32, len(queries) + 4))

        Returns:
            List[List[SearchResultItem]]: List of search result lists, where each inner list
                corresponds to the query at the same index in the input queries list

        Raises:
            ValueError: If queries list is empty or contains empty strings

        Examples:
            ```python
            queries = ["BM25 overview", "keyword search", "text matching"]
            results = retriever.batch_search_keyword(queries, "Document", top_k=3)
            # results[0] contains results for "BM25 overview"
            # results[1] contains results for "keyword search"
            # results[2] contains results for "text matching"
            ```
        """
        if not queries:
            raise ValueError("Queries list cannot be empty")

        # Validate all queries are non-empty
        for i, query in enumerate(queries):
            if not query or not query.strip():
                raise ValueError(f"Query at index {i} cannot be empty")

        # Determine number of workers
        if max_workers is None:
            max_workers = min(32, len(queries) + 4)

        try:
            self.logger.info(
                f"Performing batch keyword search for {len(queries)} queries"
            )

            # Create results list with same length as queries to maintain index alignment
            results: List[List[SearchResultItem]] = [[] for _ in queries]

            # Execute queries in parallel
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all queries
                future_to_index = {
                    executor.submit(
                        self.search_keyword,
                        query,
                        collection,
                        top_k,
                        score_threshold,
                        filter,
                    ): i
                    for i, query in enumerate(queries)
                }

                # Collect results as they complete
                for future in as_completed(future_to_index):
                    index = future_to_index[future]
                    try:
                        query_results = future.result()
                        results[index] = query_results
                        self.logger.debug(
                            f"Query {index} ('{queries[index]}') returned {len(query_results)} results"
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Query {index} ('{queries[index]}') failed: {str(e)}"
                        )
                        # Keep empty list for failed query to maintain index alignment
                        results[index] = []

            self.logger.info(
                f"Batch search completed: {len(queries)} queries processed, "
                f"{sum(len(r) for r in results)} total results"
            )
            return results

        except Exception as e:
            self.logger.error(f"Batch keyword search failed: {str(e)}")
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
                    similarity_score=None,
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
