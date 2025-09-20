"""
RAG System - A Retrieval-Augmented Generation system for LaTeX documents.

This package provides a complete RAG system for creating knowledge bases
from LaTeX documents, with support for document processing, vector storage,
retrieval operations, and answer generation.

Main Components:
- RAGSystem: Main orchestrator class
- DocumentPreprocessor: LaTeX document processing
- DataChunker: Text chunking with overlap
- EmbeddingEngine: Vector embeddings using Sentence Transformers
- VectorStore: Weaviate database interface
- Retriever: Hybrid search and retrieval

Quick Start:
    from rag_system import RAGSystem

    # Initialize the system
    rag = RAGSystem()

    # Process a document
    chunk_ids = rag.process_document("document.tex")

    # Query the knowledge base
    response = rag.query("What is the main topic?")
"""

# Configuration classes
from .config.settings import ChunkConfig, EmbeddingConfig, RAGConfig, VectorStoreConfig
from .core.data_chunker import ChunkMetadata, DataChunk, DataChunker
from .core.document_preprocessor import DocumentPreprocessor
from .core.embedding_engine import EmbeddingEngine
from .core.rag_system import RAGSystem
from .core.retriever import Retriever
from .core.vector_store import VectorStore

# Version information
from .version import __version__

__version__ = __version__

__all__ = [
    # Main system
    "RAGSystem",
    # Core components
    "DataChunk",
    "DataChunker",
    "ChunkMetadata",
    "DocumentPreprocessor",
    "EmbeddingEngine",
    "Retriever",
    "VectorStore",
    # Configuration
    "RAGConfig",
    "ChunkConfig",
    "EmbeddingConfig",
    "VectorStoreConfig",
    # Version
    "__version__",
]

# Package metadata
__author__ = "Vahid Lari"
__email__ = "vahidlari@gmail.com"
__description__ = "A RAG system for creating knowledge bases from LaTeX documents"
__url__ = "https://github.com/vahidlari/aiapps"
