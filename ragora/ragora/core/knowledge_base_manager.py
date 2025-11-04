"""Knowledge base manager for document processing and retrieval.

This module provides the KnowledgeBaseManager class that orchestrates all components
of the knowledge base system, providing a unified interface for document processing,
storage, and retrieval operations.

Key responsibilities:
- Orchestrate document preprocessing and chunking
- Manage vector store operations
- Handle retrieval and search operations
- Provide unified query interface
- Manage system configuration and state

The knowledge base manager follows the layered architecture pattern with clear separation
of concerns between storage, retrieval, and generation layers.
"""

import logging
import time
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from weaviate.classes.query import Filter

from ..config import KnowledgeBaseManagerConfig
from ..utils.email_utils.base import EmailProvider
from .chunking import DataChunker
from .database_manager import DatabaseManager
from .document_preprocessor import DocumentPreprocessor
from .email_preprocessor import EmailPreprocessor
from .embedding_engine import EmbeddingEngine
from .models import RetrievalResultItem, SearchResultItem
from .retriever import Retriever
from .vector_store import VectorStore


class SearchStrategy(Enum):
    """Search strategy enumeration."""

    SIMILAR = "similar"  # Vector similarity only
    KEYWORD = "keyword"  # BM25 keyword search only
    HYBRID = "hybrid"  # Combined vector + keyword
    AUTO = "auto"  # Automatically choose best strategy


class SearchResult(BaseModel):
    """Container for search results with query metadata.

    Provides a structured container for search results including
    the query, strategy, results list, and execution metadata.
    """

    query: str = Field(..., description="Search query text")
    strategy: str = Field(..., description="Search strategy used")
    collection: str = Field(..., description="Collection searched")
    results: List[SearchResultItem] = Field(
        default_factory=list, description="List of search result items"
    )
    total_found: int = Field(..., ge=0, description="Total number of results found")
    execution_time: float = Field(..., ge=0.0, description="Execution time in seconds")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the search",
    )


class KnowledgeBaseManager:
    """Knowledge base manager for document processing and retrieval.

    This class provides a unified interface for the complete knowledge base pipeline,
    orchestrating document processing, storage, and retrieval operations. It follows
    the layered architecture pattern with clear separation of concerns.

    Attributes:
        db_manager: DatabaseManager instance for database operations
        vector_store: VectorStore instance for document storage
        retriever: Retriever instance for search operations
        embedding_engine: EmbeddingEngine for vector embeddings
        document_preprocessor: DocumentPreprocessor for LaTeX processing
        data_chunker: DataChunker for text chunking
        logger: Logger instance for debugging and monitoring
        is_initialized: Boolean indicating if system is ready
    """

    def __init__(
        self,
        config: Optional[KnowledgeBaseManagerConfig] = None,
        weaviate_url: str = "http://localhost:8080",
    ):
        """Initialize the knowledge base manager.

        Args:
            config: RagoraConfig object with system configuration (optional)
            weaviate_url: Weaviate server URL (used if config not provided)

        Raises:
            ConnectionError: If unable to connect to Weaviate
            ValueError: If invalid parameters are provided
        """
        self.is_initialized = False
        self.logger = logging.getLogger(__name__)

        try:
            self.embedding_engine = None
            self.data_chunker = None
            self.db_manager = None
            self.vector_store = None
            self.retriever = None
            self.document_preprocessor = None
            self.email_preprocessor = None

            # Handle configuration - use provided config or create from individual parameters
            if config is not None:
                if config.embedding_config:
                    # Initialize embedding engine
                    self.embedding_engine = EmbeddingEngine(
                        model_name=config.embedding_config.model_name,
                        device=(
                            config.embedding_config.device
                            if config.embedding_config.device
                            else None
                        ),
                    )
                if config.database_manager_config:
                    weaviate_url = config.database_manager_config.url
                if config.chunk_config:
                    from .chunking import DocumentChunkingStrategy

                    custom_strategy = DocumentChunkingStrategy(
                        chunk_size=config.chunk_config.chunk_size,
                        overlap_size=config.chunk_config.overlap_size,
                    )
                    self.data_chunker = DataChunker(default_strategy=custom_strategy)

            # Initialize database manager (infrastructure layer)
            self.logger.info(f"Initializing database manager at {weaviate_url}")
            self.db_manager = DatabaseManager(url=weaviate_url)

            # Initialize vector store (storage layer)
            self.logger.info("Initializing vector store")
            self.vector_store = VectorStore(
                db_manager=self.db_manager,
                embedding_engine=(
                    self.embedding_engine if self.embedding_engine else None
                ),
            )

            # Initialize retriever (search layer)
            self.logger.info("Initializing retriever")
            self.retriever = Retriever(
                db_manager=self.db_manager,
                embedding_engine=(
                    self.embedding_engine if self.embedding_engine else None
                ),
            )

            # Initialize document preprocessor with chunking parameters
            self.logger.info("Initializing document preprocessor")
            self.document_preprocessor = DocumentPreprocessor(
                chunker=(self.data_chunker if self.data_chunker else None)
            )

            # Initialize email preprocessor with chunking parameters
            self.logger.info("Initializing email preprocessor")
            self.email_preprocessor = EmailPreprocessor(
                chunker=(self.data_chunker if self.data_chunker else None)
            )

            self.is_initialized = True
            self.logger.info("Knowledge base manager initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize knowledge base manager: {str(e)}")
            raise

    def process_documents(
        self,
        document_paths: List[str],
        document_type: str = "latex",
        collection: str = "Document",
    ) -> List[str]:
        """Process a list of documents and store them in the vector database.

        Args:
            document_paths: List of paths to the LaTeX documents
            document_type: Type of document to process ("latex", "pdf", "txt")
            collection: Collection name to store the documents
        Returns:
            List[str]: List of chunk IDs that were stored
        """
        if not self.is_initialized:
            raise RuntimeError("Knowledge base manager not initialized")

        try:
            self.logger.info(f"Processing {len(document_paths)} documents")
            chunks = self.document_preprocessor.preprocess_documents(
                document_paths, document_type
            )
            self.logger.info(f"Storing {len(chunks)} chunks in vector database")
            stored_uuids = self.vector_store.store_chunks(chunks, collection=collection)
            self.logger.info(f"Successfully processed {len(document_paths)} documents")
            self.logger.info(f"Stored {len(stored_uuids)} chunks")
            return stored_uuids
        except Exception as e:
            self.logger.error(f"Failed to process documents: {str(e)}")
            raise

    def process_document(
        self,
        document_path: str,
        document_type: str = "latex",
        collection: str = "Document",
    ) -> List[str]:
        """Process a LaTeX document and store it in the vector database.

        Args:
            document_path: Path to the LaTeX document file
            document_type: Type of document to process ("latex", "pdf", "txt")
            collection: Collection name to store the document
        Returns:
            List[str]: List of chunk IDs that were stored

        Raises:
            FileNotFoundError: If document file doesn't exist
            ValueError: If document processing fails
        """
        if not self.is_initialized:
            raise RuntimeError("Knowledge base manager not initialized")

        try:
            self.logger.info(f"Processing document: {document_path}")

            # Step 1: Preprocess the LaTeX document
            self.logger.debug(f"Step 1: Preprocessing {document_type} document")
            chunks = self.document_preprocessor.preprocess_document(
                document_path, document_type
            )

            # Step 2: Store chunks in vector database
            self.logger.debug(
                f"Step 2: Storing {len(chunks)} chunks in vector database"
            )
            stored_uuids = self.vector_store.store_chunks(chunks, collection=collection)

            self.logger.info(f"Successfully processed document: {document_path}")
            self.logger.info(f"Stored {len(stored_uuids)} chunks")

            return stored_uuids

        except Exception as e:
            self.logger.error(f"Failed to process document {document_path}: {str(e)}")
            raise

    def search(
        self,
        query: str,
        collection: str = "Document",
        strategy: SearchStrategy = SearchStrategy.HYBRID,
        top_k: int = 5,
        filter: Optional[Filter] = None,
        **strategy_kwargs,
    ) -> SearchResult:
        """Unified search interface for all data types and strategies.

        Args:
            query: Search query text
            collection: Collection name to search in
            strategy: Search strategy to use
            top_k: Number of results to return
            filter: Optional Weaviate Filter to filter results by properties
            **strategy_kwargs: Strategy-specific parameters
                (alpha, score_threshold, etc.)

        Returns:
            SearchResult: Structured search results with metadata

        Raises:
            RuntimeError: If system not initialized
            ValueError: If invalid strategy or empty query
        """
        if not self.is_initialized:
            raise RuntimeError("Knowledge base manager not initialized")

        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        start_time = time.time()

        try:
            self.logger.info(
                f"Processing search: '{query}' "
                f"(strategy: {strategy.value if hasattr(strategy, 'value') else strategy}, collection: {collection})"
            )

            # Execute search based on strategy
            if strategy == SearchStrategy.SIMILAR:
                results = self.retriever.search_similar(
                    query,
                    collection=collection,
                    top_k=top_k,
                    filter=filter,
                    **strategy_kwargs,
                )
            elif strategy == SearchStrategy.KEYWORD:
                results = self.retriever.search_keyword(
                    query,
                    collection=collection,
                    top_k=top_k,
                    filter=filter,
                    **strategy_kwargs,
                )
            elif strategy == SearchStrategy.HYBRID:
                results = self.retriever.search_hybrid(
                    query,
                    collection=collection,
                    top_k=top_k,
                    filter=filter,
                    **strategy_kwargs,
                )
            elif strategy == SearchStrategy.AUTO:
                # For now, default to hybrid.
                # Could be enhanced with automatic strategy selection
                results = self.retriever.search_hybrid(
                    query,
                    collection=collection,
                    top_k=top_k,
                    filter=filter,
                    **strategy_kwargs,
                )
            else:
                raise ValueError(f"Invalid search strategy: {strategy}")

            execution_time = time.time() - start_time

            # Prepare metadata
            metadata = {
                "chunk_sources": list(
                    set(
                        result.properties.get("source_document", "")
                        or result.metadata.source_document
                        or ""
                        for result in results
                    )
                ),
                "chunk_types": list(
                    set(
                        result.properties.get("chunk_type", "")
                        or result.metadata.chunk_type
                        or ""
                        for result in results
                    )
                ),
            }

            # Add similarity scores if available
            if results:
                metadata["avg_similarity"] = sum(
                    result.similarity_score for result in results
                ) / len(results)
                metadata["max_similarity"] = max(
                    result.similarity_score for result in results
                )

            self.logger.info(
                f"Search completed: {len(results)} results in {execution_time:.3f}s"
            )

            # Convert strategy enum to string for SearchResult
            strategy_str = (
                strategy.value if hasattr(strategy, "value") else str(strategy)
            )

            results_dicts = [item.model_dump() for item in results]

            # Use model_validate for proper nested model validation in Pydantic 2.x
            return SearchResult.model_validate(
                {
                    "query": query,
                    "strategy": strategy_str,
                    "collection": collection,
                    "results": results_dicts,
                    "total_found": len(results),
                    "execution_time": execution_time,
                    "metadata": metadata,
                }
            )

        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            raise

    def get_chunk(
        self, chunk_id: str, collection: str
    ) -> Optional[RetrievalResultItem]:
        """Retrieve a specific chunk by its ID.

        Args:
            chunk_id: Unique identifier of the chunk
            collection: Collection name
        Returns:
            Optional[RetrievalResultItem]: Chunk data if found, None otherwise
        """
        return self.vector_store.get_chunk_by_id(chunk_id, collection=collection)

    def delete_chunk(self, chunk_id: str, collection: str) -> bool:
        """Delete a chunk by its ID.

        Args:
            chunk_id: Unique identifier of the chunk to delete
            collection: Collection name
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        return self.vector_store.delete_chunk(chunk_id, collection=collection)

    def list_collections(self) -> List[str]:
        """List all available collections.

        Returns:
            List[str]: List of collection names
        """
        return self.db_manager.list_collections()

    def create_collection(self, name: str, force_recreate: bool = False) -> bool:
        """Create a new collection.

        Args:
            name: Collection name
            force_recreate: Whether to recreate if collection exists

        Returns:
            bool: True if creation was successful, False otherwise
        """
        try:
            self.vector_store.create_schema(name, force_recreate=force_recreate)
            return True
        except Exception as e:
            self.logger.error(f"Failed to create collection {name}: {e}")
            return False

    def delete_collection(self, name: str) -> bool:
        """Delete a collection and all its data.

        Args:
            name: Collection name

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            self.vector_store.clear_all(collection=name)
            # Note: Weaviate doesn't have direct collection deletion
            # This clears all data, effectively "deleting" the collection
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete collection {name}: {e}")
            return False

    def clear_collection(self, collection: str) -> None:
        """Clear all data from a collection.

        Args:
            collection: Collection name

        Raises:
            RuntimeError: If system not initialized
        """
        if not self.is_initialized:
            raise RuntimeError("Knowledge base manager not initialized")

        try:
            self.logger.warning(f"Clearing all data from collection: {collection}")
            self.vector_store.clear_all(collection=collection)
            self.logger.info(f"Collection {collection} cleared successfully")
        except Exception as e:
            self.logger.error(f"Failed to clear collection {collection}: {str(e)}")
            raise

    def get_collection_stats(self, collection: str) -> Dict[str, Any]:
        """Get statistics for a specific collection.

        Args:
            collection: Collection name

        Returns:
            Dict[str, Any]: Collection statistics
        """
        try:
            # Get vector store stats
            vector_stats = self.vector_store.get_stats(collection=collection)

            # Get retrieval stats
            retrieval_stats = self.retriever.get_retrieval_stats(collection=collection)

            # Get embedding engine info
            embedding_info = (
                self.embedding_engine.get_model_info()
                if self.embedding_engine
                else {"model_name": "Not initialized", "dimension": None}
            )

            # Get chunker configuration
            chunker_config = (
                {
                    "chunk_size": self.data_chunker.default_strategy.chunk_size,
                    "overlap_size": self.data_chunker.default_strategy.overlap_size,
                    "chunk_type": "custom",
                }
                if self.data_chunker
                else {
                    "chunk_size": "Not initialized",
                    "overlap_size": "Not initialized",
                    "chunk_type": "Not initialized",
                }
            )

            return {
                "collection": collection,
                "system_initialized": self.is_initialized,
                "database_manager": {
                    "url": self.db_manager.url,
                    "is_connected": self.db_manager.is_connected,
                    "collections": self.db_manager.list_collections(),
                },
                "vector_store": vector_stats,
                "retrieval": retrieval_stats,
                "embedding_engine": embedding_info,
                "data_chunker": chunker_config,
                "components": {
                    "database_manager": "Weaviate Infrastructure",
                    "vector_store": "Weaviate Storage",
                    "retriever": "Weaviate Search APIs",
                    "embedding_engine": embedding_info["model_name"],
                    "document_preprocessor": "LaTeX Parser",
                },
                "architecture": "Three-Layer (DatabaseManager -> VectorStore -> Retriever)",
            }

        except Exception as e:
            self.logger.error(f"Failed to get collection stats: {str(e)}")
            raise

    def close(self) -> None:
        """Close all system connections and cleanup resources."""
        try:
            if hasattr(self, "vector_store"):
                self.vector_store.close()
            self.is_initialized = False
            self.logger.info("Knowledge base manager closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing knowledge base manager: {str(e)}")

    # Email processing methods

    def _ensure_email_connection(self, email_provider: EmailProvider) -> bool:
        """Ensure email provider is connected.

        Returns True if we connected it, False if already connected.
        """
        if not email_provider.is_connected:
            self.logger.debug("Email provider not connected, connecting...")
            email_provider.connect()
            return True
        return False

    def check_new_emails(
        self,
        email_provider: EmailProvider,
        folder: Optional[str] = None,
        include_body: bool = True,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Check for new unread emails without storing them.

        Args:
            email_provider: Email provider instance
            folder: Optional folder to check (None = all folders)
            include_body: Include email body content (default: True)
            limit: Maximum number of emails to return

        Returns:
            Dictionary with count and email metadata
        """
        if not self.is_initialized:
            raise RuntimeError("Knowledge base manager not initialized")

        try:
            # Auto-connect if needed
            self._ensure_email_connection(email_provider)

            # Fetch unread messages
            new_emails = email_provider.fetch_messages(
                limit=limit, folder=folder, unread_only=True
            )

            # Build result
            emails_data = []
            for email in new_emails:
                email_data = {
                    "email_id": email.message_id,
                    "subject": email.subject,
                    "sender": str(email.sender) if email.sender else "",
                    "date_sent": (
                        email.date_sent.isoformat() if email.date_sent else None
                    ),
                    "folder": email.folder if hasattr(email, "folder") else None,
                }

                if include_body:
                    email_data["body"] = email.get_body()

                emails_data.append(email_data)

            result = {"count": len(new_emails), "emails": emails_data}

            self.logger.info(f"Found {len(new_emails)} new emails")
            return result

        except Exception as e:
            self.logger.error(f"Failed to check new emails: {str(e)}")
            raise

    def process_new_emails(
        self,
        email_provider: EmailProvider,
        email_ids: List[str],
        collection: str = "Email",
    ) -> List[str]:
        """Process and store specific emails by their IDs.

        This method processes emails that have been identified by the user
        through check_new_emails() and filtered as needed.

        Args:
            email_provider: Email provider instance
            email_ids: List of email IDs to process (required)
            collection: Collection name to store the emails

        Returns:
            List of stored chunk IDs
        """
        if not self.is_initialized:
            raise RuntimeError("Knowledge base manager not initialized")

        if not email_ids:
            self.logger.warning("No email IDs provided")
            return []

        try:
            # Auto-connect if needed
            self._ensure_email_connection(email_provider)

            # Fetch specific emails by ID
            emails = []
            for email_id in email_ids:
                email = email_provider.fetch_message_by_id(email_id)
                if email:
                    emails.append(email)
                else:
                    self.logger.warning(f"Email {email_id} not found")

            if not emails:
                self.logger.info("No emails found to process")
                return []

            # Preprocess emails
            self.logger.info(f"Preprocessing {len(emails)} emails")
            chunks = self.email_preprocessor.preprocess_emails(emails)

            # Store chunks
            self.logger.info(f"Storing {len(chunks)} chunks")
            stored_uuids = self.vector_store.store_chunks(chunks, collection=collection)

            self.logger.info(f"Successfully processed {len(emails)} emails")
            return stored_uuids

        except Exception as e:
            self.logger.error(f"Failed to process new emails: {str(e)}")
            raise

    def process_email_account(
        self,
        email_provider: EmailProvider,
        folder: Optional[str] = None,
        unread_only: bool = False,
        collection: str = "Email",
    ) -> List[str]:
        """Process emails from an email account.

        Args:
            email_provider: Email provider instance
            folder: Optional folder to process (None = all folders)
            unread_only: If True, only process unread emails
            collection: Collection name to store the emails

        Returns:
            List of stored chunk IDs
        """
        if not self.is_initialized:
            raise RuntimeError("Knowledge base manager not initialized")

        try:
            # Auto-connect if needed
            self._ensure_email_connection(email_provider)

            # Fetch emails
            emails = email_provider.fetch_messages(
                limit=None, folder=folder, unread_only=unread_only
            )

            if not emails:
                self.logger.info("No emails to process")
                return []

            # Preprocess emails
            self.logger.info(f"Preprocessing {len(emails)} emails")
            chunks = self.email_preprocessor.preprocess_emails(emails)

            # Store chunks
            self.logger.info(f"Storing {len(chunks)} chunks")
            stored_uuids = self.vector_store.store_chunks(chunks, collection=collection)

            self.logger.info(f"Successfully processed {len(emails)} emails")
            return stored_uuids

        except Exception as e:
            self.logger.error(f"Failed to process email account: {str(e)}")
            raise

    def process_emails(
        self,
        email_provider: EmailProvider,
        email_ids: List[str],
        collection: str = "Email",
    ) -> List[str]:
        """Process specific emails by their IDs.

        Args:
            email_provider: Email provider instance
            email_ids: List of email IDs to process
            collection: Collection name to store the emails

        Returns:
            List of stored chunk IDs
        """
        if not self.is_initialized:
            raise RuntimeError("Knowledge base manager not initialized")

        try:
            # Auto-connect if needed
            self._ensure_email_connection(email_provider)

            # Fetch emails
            emails = []
            for email_id in email_ids:
                email = email_provider.fetch_message_by_id(email_id)
                if email:
                    emails.append(email)

            if not emails:
                self.logger.info("No emails found to process")
                return []

            # Preprocess emails
            self.logger.info(f"Preprocessing {len(emails)} emails")
            chunks = self.email_preprocessor.preprocess_emails(emails)

            # Store chunks
            self.logger.info(f"Storing {len(chunks)} chunks")
            stored_uuids = self.vector_store.store_chunks(chunks, collection=collection)

            self.logger.info(f"Successfully processed {len(emails)} emails")
            return stored_uuids

        except Exception as e:
            self.logger.error(f"Failed to process emails: {str(e)}")
            raise

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
