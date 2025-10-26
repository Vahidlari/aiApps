"""Core modules for the LaTeX RAG system.

This package contains the core functionality for document processing,
embedding generation, vector storage, retrieval operations, and the
main RAG system orchestrator.
"""

from .chunking import (
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
from .database_manager import DatabaseManager
from .document_preprocessor import DocumentPreprocessor
from .embedding_engine import EmbeddingEngine
from .knowledge_base_manager import KnowledgeBaseManager
from .retriever import Retriever
from .vector_store import VectorStore

__all__ = [
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
    "EmbeddingEngine",
    "KnowledgeBaseManager",
    "Retriever",
    "VectorStore",
]
