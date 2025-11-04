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
    from ragora import KnowledgeBaseManager, SearchStrategy

    # Initialize the system with three-layer architecture
    kbm = KnowledgeBaseManager(
        weaviate_url="http://localhost:8080"
    )

    # Process documents
    chunk_ids = kbm.process_documents(["document.tex"])

    # Query the knowledge base with different search strategies
    response = kbm.search("What is the main topic?", strategy=SearchStrategy.SIMILAR)
    hybrid_response = kbm.search("machine learning", strategy=SearchStrategy.HYBRID)
    keyword_response = kbm.search("neural networks", strategy=SearchStrategy.KEYWORD)
"""

# Configuration classes
from .config.settings import (
    ChunkConfig,
    DatabaseManagerConfig,
    EmbeddingConfig,
    KnowledgeBaseManagerConfig,
)
from .core.chunking import (
    ChunkingContext,
    ChunkingContextBuilder,
    ChunkingStrategy,
    ChunkMetadata,
    DataChunk,
    DataChunker,
    DocumentChunkingStrategy,
    EmailChunkingStrategy,
    TextChunkingStrategy,
)
from .core.database_manager import DatabaseManager
from .core.document_preprocessor import DocumentPreprocessor
from .core.email_preprocessor import EmailPreprocessor
from .core.embedding_engine import EmbeddingEngine
from .core.filters import FilterBuilder
from .core.knowledge_base_manager import (
    KnowledgeBaseManager,
    SearchResult,
    SearchStrategy,
)
from .core.models import RetrievalMetadata, RetrievalResultItem, SearchResultItem
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
    "SearchStrategy",
    "SearchResult",
    "SearchResultItem",
    "RetrievalMetadata",
    "RetrievalResultItem",
    # Core components
    "DataChunk",
    "DataChunker",
    "ChunkMetadata",
    "ChunkingContext",
    "ChunkingContextBuilder",
    "ChunkingStrategy",
    "TextChunkingStrategy",
    "DocumentChunkingStrategy",
    "EmailChunkingStrategy",
    "DatabaseManager",
    "DocumentPreprocessor",
    "EmailPreprocessor",
    "EmbeddingEngine",
    "FilterBuilder",
    "Retriever",
    "VectorStore",
    # Configuration
    "KnowledgeBaseManagerConfig",
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
