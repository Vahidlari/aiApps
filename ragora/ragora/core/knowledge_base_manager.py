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
from typing import Any, Dict, List, Optional

from ..config import KnowledgeBaseManagerConfig
from ..utils.email_utils.base import EmailProvider
from .chunking import DataChunker
from .database_manager import DatabaseManager
from .document_preprocessor import DocumentPreprocessor
from .email_preprocessor import EmailPreprocessor
from .embedding_engine import EmbeddingEngine
from .retriever import Retriever
from .vector_store import VectorStore


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
        class_name: str = "Document",
    ):
        """Initialize the knowledge base manager.

        Args:
            config: RagoraConfig object with system configuration (optional)
            weaviate_url: Weaviate server URL (used if config not provided)
            class_name: Name of the Weaviate class for document storage (used if config not provided)

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
        class_name: str = "Document",
    ) -> List[str]:
        """Process a list of documents and store them in the vector database.

        Args:
            document_paths: List of paths to the LaTeX documents
            document_type: Type of document to process ("latex", "pdf", "txt")
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
            stored_uuids = self.vector_store.store_chunks(chunks, class_name=class_name)
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
        class_name: str = "Document",
    ) -> List[str]:
        """Process a LaTeX document and store it in the vector database.

        Args:
            document_path: Path to the LaTeX document file
            document_type: Type of document to process ("latex", "pdf", "txt")
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
            stored_uuids = self.vector_store.store_chunks(chunks, class_name=class_name)

            self.logger.info(f"Successfully processed document: {document_path}")
            self.logger.info(f"Stored {len(stored_uuids)} chunks")

            return stored_uuids

        except Exception as e:
            self.logger.error(f"Failed to process document {document_path}: {str(e)}")
            raise

    def query(
        self,
        question: str,
        search_type: str = "similar",
        top_k: int = 5,
        class_name: str = "Document",
    ) -> Dict[str, Any]:
        """Query the knowledge base with a question.

        Args:
            question: The question to ask
            search_type: Type of search ("similar", "hybrid", "citations", "equations")
            top_k: Number of relevant chunks to retrieve

        Returns:
            Dict[str, Any]: Query results with retrieved chunks and metadata

        Raises:
            RuntimeError: If system not initialized
            ValueError: If invalid search type or empty question
        """
        if not self.is_initialized:
            raise RuntimeError("Knowledge base manager not initialized")

        if not question or not question.strip():
            raise ValueError("Question cannot be empty")

        try:
            self.logger.info(f"Processing query: '{question}' (type: {search_type})")

            # Step 1: Retrieve relevant chunks
            self.logger.debug("Step 1: Retrieving relevant chunks")
            if search_type == "similar":
                chunks = self.retriever.search_similar(
                    question, top_k=top_k, class_name=class_name
                )
            elif search_type == "hybrid":
                chunks = self.retriever.search_hybrid(
                    question, top_k=top_k, class_name=class_name
                )
            elif search_type == "keyword":
                chunks = self.retriever.search_keyword(
                    question, top_k=top_k, class_name=class_name
                )
            else:
                raise ValueError(
                    f"Invalid search type: {search_type}. "
                    f"Supported types: 'similar', 'hybrid', 'keyword'"
                )

            # Step 2: Prepare response
            self.logger.debug(f"Step 2: Preparing response with {len(chunks)} chunks")
            response = {
                "question": question,
                "search_type": search_type,
                "retrieved_chunks": chunks,
                "num_chunks": len(chunks),
                "chunk_sources": list(
                    set(chunk.get("source_document", "") for chunk in chunks)
                ),
                "chunk_types": list(
                    set(chunk.get("chunk_type", "") for chunk in chunks)
                ),
            }

            # Add similarity scores if available
            if chunks and "similarity_score" in chunks[0]:
                response["avg_similarity"] = sum(
                    chunk.get("similarity_score", 0) for chunk in chunks
                ) / len(chunks)
                response["max_similarity"] = max(
                    chunk.get("similarity_score", 0) for chunk in chunks
                )

            self.logger.info(f"Query completed: {len(chunks)} chunks retrieved")
            return response

        except Exception as e:
            self.logger.error(f"Query failed: {str(e)}")
            raise

    def search_similar(
        self, query: str, top_k: int = 5, class_name: str = "Document"
    ) -> List[Dict[str, Any]]:
        """Search for similar documents using vector similarity.

        Args:
            query: Search query text
            top_k: Number of results to return
            class_name: Name of the Weaviate class for document storage

        Returns:
            List[Dict[str, Any]]: List of search results with metadata
        """
        return self.retriever.search_similar(query, top_k=top_k, class_name=class_name)

    def search_hybrid(
        self,
        query: str,
        alpha: float = 0.5,
        top_k: int = 5,
        class_name: str = "Document",
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search combining vector and keyword search.

        Args:
            query: Search query text
            alpha: Weight for vector search (0.0 = keyword only, 1.0 = vector only)
            top_k: Number of results to return
            class_name: Name of the Weaviate class for document storage

        Returns:
            List[Dict[str, Any]]: List of search results with metadata
        """
        return self.retriever.search_hybrid(
            query, alpha=alpha, top_k=top_k, class_name=class_name
        )

    def search_keyword(
        self,
        query: str,
        top_k: int = 5,
        class_name: str = "Document",
    ) -> List[Dict[str, Any]]:
        """Perform keyword search.

        Args:
            query: Search query text
            top_k: Number of results to return
            filters: Optional filters to apply to the search

        Returns:
            List[Dict[str, Any]]: List of search results with metadata
        """
        return self.retriever.search_keyword(query, top_k=top_k, class_name=class_name)

    def get_chunk(self, chunk_id: str, class_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific chunk by its ID.

        Args:
            chunk_id: Unique identifier of the chunk
            class_name: Name of the Weaviate class for document storage
        Returns:
            Optional[Dict[str, Any]]: Chunk data if found, None otherwise
        """
        return self.vector_store.get_chunk_by_id(chunk_id, class_name=class_name)

    def delete_chunk(self, chunk_id: str, class_name: str) -> bool:
        """Delete a chunk by its ID.

        Args:
            chunk_id: Unique identifier of the chunk to delete
            class_name: Name of the Weaviate class for document storage
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        return self.vector_store.delete_chunk(chunk_id, class_name=class_name)

    def get_system_stats(self, class_name: str) -> Dict[str, Any]:
        """Get comprehensive system statistics.

        Args:
            class_name: Name of the Weaviate class for document storage

        Returns:
            Dict[str, Any]: System statistics including storage, retrieval, and configuration info
        """
        try:
            # Get vector store stats
            vector_stats = self.vector_store.get_stats(class_name=class_name)

            # Get retrieval stats
            retrieval_stats = self.retriever.get_retrieval_stats(class_name=class_name)

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
            self.logger.error(f"Failed to get system stats: {str(e)}")
            raise

    def clear_database(self, class_name: str) -> None:
        """Clear all data from the vector database.

        Args:
            class_name: Name of the Weaviate class for document storage

        Raises:
            RuntimeError: If system not initialized
        """
        if not self.is_initialized:
            raise RuntimeError("Knowledge base manager not initialized")

        try:
            self.logger.warning("Clearing all data from vector database")
            self.vector_store.clear_all(class_name=class_name)
            self.logger.info("Database cleared successfully")
        except Exception as e:
            self.logger.error(f"Failed to clear database: {str(e)}")
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
        class_name: str = "Email",
    ) -> List[str]:
        """Process and store specific emails by their IDs.

        This method processes emails that have been identified by the user
        through check_new_emails() and filtered as needed.

        Args:
            email_provider: Email provider instance
            email_ids: List of email IDs to process (required)
            class_name: Vector store collection name

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
            stored_uuids = self.vector_store.store_chunks(chunks, class_name=class_name)

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
        class_name: str = "Email",
    ) -> List[str]:
        """Process emails from an email account.

        Args:
            email_provider: Email provider instance
            folder: Optional folder to process (None = all folders)
            unread_only: If True, only process unread emails
            class_name: Vector store collection name

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
            stored_uuids = self.vector_store.store_chunks(chunks, class_name=class_name)

            self.logger.info(f"Successfully processed {len(emails)} emails")
            return stored_uuids

        except Exception as e:
            self.logger.error(f"Failed to process email account: {str(e)}")
            raise

    def process_emails(
        self,
        email_provider: EmailProvider,
        email_ids: List[str],
        class_name: str = "Email",
    ) -> List[str]:
        """Process specific emails by their IDs.

        Args:
            email_provider: Email provider instance
            email_ids: List of email IDs to process
            class_name: Vector store collection name

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
            stored_uuids = self.vector_store.store_chunks(chunks, class_name=class_name)

            self.logger.info(f"Successfully processed {len(emails)} emails")
            return stored_uuids

        except Exception as e:
            self.logger.error(f"Failed to process emails: {str(e)}")
            raise

    def search_emails(
        self,
        query: str,
        search_type: str = "similar",
        top_k: int = 5,
        class_name: str = "Email",
    ) -> List[Dict[str, Any]]:
        """Search emails in the knowledge base.

        Args:
            query: Search query text
            search_type: Type of search ("similar", "hybrid", "keyword")
            top_k: Number of results to return
            class_name: Vector store collection name

        Returns:
            List of search results with metadata
        """
        if not self.is_initialized:
            raise RuntimeError("Knowledge base manager not initialized")

        # Use existing retriever methods with class_name
        if search_type == "similar":
            return self.retriever.search_similar(
                query, top_k=top_k, class_name=class_name
            )
        elif search_type == "hybrid":
            return self.retriever.search_hybrid(
                query, top_k=top_k, class_name=class_name
            )
        elif search_type == "keyword":
            return self.retriever.search_keyword(
                query, top_k=top_k, class_name=class_name
            )
        else:
            raise ValueError(f"Invalid search type: {search_type}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
