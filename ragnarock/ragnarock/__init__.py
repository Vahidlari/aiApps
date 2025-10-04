"""
RAG System - A Retrieval-Augmented Generation system for LaTeX documents.

This package provides a complete RAG system for creating knowledge bases
from LaTeX documents, with support for document processing, vector storage,
retrieval operations, and answer generation.

Main Components (Three-Layer Architecture):
- KnowledgeBaseManager: Main orchestrator class
- DatabaseManager: Infrastructure layer for Weaviate operations
- VectorStore: Storage layer for document persistence
- Retriever: Search layer using Weaviate APIs directly
- DocumentPreprocessor: LaTeX document processing
- DataChunker: Text chunking with overlap
- EmbeddingEngine: Vector embeddings using Sentence Transformers

Quick Start:
    from ragnarock import KnowledgeBaseManager

    # Initialize the system with three-layer architecture
    kbm = KnowledgeBaseManager(
        weaviate_url="http://localhost:8080",
        class_name="Document",
        embedding_model="all-mpnet-base-v2"
    )

    # Process documents
    chunk_ids = kbm.process_documents(["document.tex"])

    # Query the knowledge base with different search types
    response = kbm.query("What is the main topic?", search_type="similar")
    hybrid_response = kbm.query("machine learning", search_type="hybrid")
    keyword_response = kbm.query("neural networks", search_type="keyword")
"""

# Configuration classes
from .config.settings import (
    ChunkConfig,
    DatabaseManagerConfig,
    EmbeddingConfig,
    RAGConfig,
)
from .core.data_chunker import ChunkMetadata, DataChunk, DataChunker
from .core.database_manager import DatabaseManager
from .core.document_preprocessor import DocumentPreprocessor
from .core.embedding_engine import EmbeddingEngine
from .core.knowledge_base_manager import KnowledgeBaseManager
from .core.retriever import Retriever
from .core.vector_store import VectorStore
from .exceptions import (
    ConfigurationError,
    DocumentProcessingError,
    EmbeddingError,
    KnowledgeBaseManagerError,
    RetrievalError,
    VectorStoreError,
)

# Version information
from .version import __version__

__version__ = __version__

__all__ = [
    # Main system
    "KnowledgeBaseManager",
    # Core components
    "DataChunk",
    "DataChunker",
    "ChunkMetadata",
    "DatabaseManager",
    "DocumentPreprocessor",
    "EmbeddingEngine",
    "Retriever",
    "VectorStore",
    # Configuration
    "RAGConfig",
    "ChunkConfig",
    "EmbeddingConfig",
    "DatabaseManagerConfig",
    # Exceptions
    "KnowledgeBaseManagerError",
    "ConfigurationError",
    "DocumentProcessingError",
    "VectorStoreError",
    "RetrievalError",
    "EmbeddingError",
    # Version
    "__version__",
]

# Package metadata
__author__ = "Vahid Lari"
__email__ = "vahidlari@gmail.com"
__description__ = "A knowledge base manager for LaTeX documents"
__url__ = "https://github.com/vahidlari/aiapps"
