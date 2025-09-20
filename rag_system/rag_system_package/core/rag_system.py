"""Main RAG system orchestrator.

This module provides the RAGSystem class that orchestrates all components
of the RAG (Retrieval-Augmented Generation) system, providing a unified interface
for document processing, storage, retrieval, and generation.

Key responsibilities:
- Orchestrate document preprocessing and chunking
- Manage vector store operations
- Handle retrieval and search operations
- Coordinate with generation system
- Provide unified query interface
- Manage system configuration and state

The RAG system follows the layered architecture pattern with clear separation
of concerns between storage, retrieval, and generation layers.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from .data_chunker import DataChunk, DataChunker
from .document_preprocessor import DocumentPreprocessor
from .embedding_engine import EmbeddingEngine
from .retriever import Retriever
from .vector_store import VectorStore


class RAGSystem:
    """Main RAG system orchestrator.

    This class provides a unified interface for the complete RAG pipeline,
    orchestrating document processing, storage, retrieval, and generation
    operations. It follows the layered architecture pattern with clear
    separation of concerns.

    Attributes:
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
        config: Optional[Any] = None,
        weaviate_url: str = "http://localhost:8080",
        class_name: str = "Document",
        embedding_model: str = "all-mpnet-base-v2",
        chunk_size: int = 768,
        chunk_overlap: int = 100,
    ):
        """Initialize the RAG system.

        Args:
            config: RAGConfig object with system configuration (optional)
            weaviate_url: Weaviate server URL (used if config not provided)
            class_name: Name of the Weaviate class for document storage (used if config not provided)
            embedding_model: Name of the embedding model to use (used if config not provided)
            chunk_size: Size of text chunks in tokens (used if config not provided)
            chunk_overlap: Overlap between chunks in tokens (used if config not provided)

        Raises:
            ConnectionError: If unable to connect to Weaviate
            ValueError: If invalid parameters are provided
        """
        self.is_initialized = False
        self.logger = logging.getLogger(__name__)

        try:
            # Handle configuration - use provided config or create from individual parameters
            if config is not None:
                embedding_model = config.embedding_config.model_name
                weaviate_url = config.vector_store_config.url
                class_name = config.vector_store_config.class_name
                chunk_size = config.chunk_config.chunk_size
                chunk_overlap = config.chunk_config.overlap

            # Initialize embedding engine
            self.logger.info(
                f"Initializing embedding engine with model: {embedding_model}"
            )
            self.embedding_engine = EmbeddingEngine(model_name=embedding_model)

            # Initialize vector store
            self.logger.info(f"Initializing vector store at {weaviate_url}")
            self.vector_store = VectorStore(
                url=weaviate_url,
                class_name=class_name,
                embedding_engine=self.embedding_engine,
            )

            # Initialize retriever
            self.logger.info("Initializing retriever")
            self.retriever = Retriever(
                vector_store=self.vector_store,
                embedding_engine=self.embedding_engine,
            )

            # Initialize document preprocessor
            self.logger.info("Initializing document preprocessor")
            self.document_preprocessor = DocumentPreprocessor()

            # Initialize data chunker
            self.logger.info(
                f"Initializing data chunker (size={chunk_size}, overlap={chunk_overlap})"
            )
            self.data_chunker = DataChunker(
                chunk_size=chunk_size,
                overlap=chunk_overlap,
            )

            self.is_initialized = True
            self.logger.info("RAG system initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize RAG system: {str(e)}")
            raise

    def process_document(self, document_path: str) -> List[str]:
        """Process a LaTeX document and store it in the vector database.

        Args:
            document_path: Path to the LaTeX document file

        Returns:
            List[str]: List of chunk IDs that were stored

        Raises:
            FileNotFoundError: If document file doesn't exist
            ValueError: If document processing fails
        """
        if not self.is_initialized:
            raise RuntimeError("RAG system not initialized")

        try:
            self.logger.info(f"Processing document: {document_path}")

            # Step 1: Preprocess the LaTeX document
            self.logger.debug("Step 1: Preprocessing LaTeX document")
            processed_doc = self.document_preprocessor.preprocess_document(
                document_path
            )

            # Step 2: Chunk the processed document
            self.logger.debug("Step 2: Chunking processed document")
            chunks = self.data_chunker.chunk_document(processed_doc)

            # Step 3: Store chunks in vector database
            self.logger.debug(
                f"Step 3: Storing {len(chunks)} chunks in vector database"
            )
            stored_uuids = self.vector_store.store_chunks(chunks)

            self.logger.info(f"Successfully processed document: {document_path}")
            self.logger.info(f"Stored {len(stored_uuids)} chunks")

            return stored_uuids

        except Exception as e:
            self.logger.error(f"Failed to process document {document_path}: {str(e)}")
            raise

    def query(
        self, question: str, search_type: str = "similar", top_k: int = 5
    ) -> Dict[str, Any]:
        """Query the RAG system with a question.

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
            raise RuntimeError("RAG system not initialized")

        if not question or not question.strip():
            raise ValueError("Question cannot be empty")

        try:
            self.logger.info(f"Processing query: '{question}' (type: {search_type})")

            # Step 1: Retrieve relevant chunks
            self.logger.debug("Step 1: Retrieving relevant chunks")
            if search_type == "similar":
                chunks = self.retriever.search_similar(question, top_k=top_k)
            elif search_type == "hybrid":
                chunks = self.retriever.search_hybrid(question, top_k=top_k)
            else:
                raise ValueError(
                    f"Invalid search type: {search_type}. "
                    f"Supported types: 'similar', 'hybrid'"
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
        self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents using vector similarity.

        Args:
            query: Search query text
            top_k: Number of results to return
            filters: Optional filters to apply to the search

        Returns:
            List[Dict[str, Any]]: List of search results with metadata
        """
        return self.retriever.search_similar(query, top_k=top_k, filters=filters)

    def search_hybrid(
        self,
        query: str,
        alpha: float = 0.5,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search combining vector and keyword search.

        Args:
            query: Search query text
            alpha: Weight for vector search (0.0 = keyword only, 1.0 = vector only)
            top_k: Number of results to return
            filters: Optional filters to apply to the search

        Returns:
            List[Dict[str, Any]]: List of search results with metadata
        """
        return self.retriever.search_hybrid(
            query, alpha=alpha, top_k=top_k, filters=filters
        )

    def get_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific chunk by its ID.

        Args:
            chunk_id: Unique identifier of the chunk

        Returns:
            Optional[Dict[str, Any]]: Chunk data if found, None otherwise
        """
        return self.vector_store.get_chunk_by_id(chunk_id)

    def delete_chunk(self, chunk_id: str) -> bool:
        """Delete a chunk by its ID.

        Args:
            chunk_id: Unique identifier of the chunk to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        return self.vector_store.delete_chunk(chunk_id)

    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics.

        Returns:
            Dict[str, Any]: System statistics including storage, retrieval, and configuration info
        """
        try:
            # Get vector store stats
            vector_stats = self.vector_store.get_stats()

            # Get retrieval stats
            retrieval_stats = self.retriever.get_retrieval_stats()

            # Get embedding engine info
            embedding_info = self.embedding_engine.get_model_info()

            # Get chunker configuration
            chunker_config = {
                "chunk_size": self.data_chunker.chunk_size,
                "overlap": self.data_chunker.overlap,
                "chunking_strategy": "adaptive_fixed_size",
            }

            return {
                "system_initialized": self.is_initialized,
                "vector_store": vector_stats,
                "retrieval": retrieval_stats,
                "embedding_engine": embedding_info,
                "data_chunker": chunker_config,
                "components": {
                    "vector_store": "Weaviate",
                    "retriever": "Hybrid Search",
                    "embedding_engine": embedding_info["model_name"],
                    "document_preprocessor": "LaTeX Parser",
                },
            }

        except Exception as e:
            self.logger.error(f"Failed to get system stats: {str(e)}")
            raise

    def clear_database(self) -> None:
        """Clear all data from the vector database.

        Raises:
            RuntimeError: If system not initialized
        """
        if not self.is_initialized:
            raise RuntimeError("RAG system not initialized")

        try:
            self.logger.warning("Clearing all data from vector database")
            self.vector_store.clear_all()
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
            self.logger.info("RAG system closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing RAG system: {str(e)}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
