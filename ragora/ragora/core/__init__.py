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
from .email_preprocessor import EmailPreprocessor
from .embedding_engine import EmbeddingEngine
from .filters import FilterBuilder
from .knowledge_base_manager import KnowledgeBaseManager, SearchResult, SearchStrategy
from .models import RetrievalMetadata, RetrievalResultItem, SearchResultItem
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
    "EmailPreprocessor",
    "EmbeddingEngine",
    "FilterBuilder",
    "KnowledgeBaseManager",
    "SearchStrategy",
    "SearchResult",
    "SearchResultItem",
    "RetrievalMetadata",
    "RetrievalResultItem",
    "Retriever",
    "VectorStore",
]
