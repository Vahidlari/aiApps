"""Custom exceptions for the RAG system."""


class RAGSystemError(Exception):
    """Base exception for RAG system errors."""

    pass


class ConfigurationError(RAGSystemError):
    """Raised when there's a configuration error."""

    pass


class DocumentProcessingError(RAGSystemError):
    """Raised when document processing fails."""

    pass


class VectorStoreError(RAGSystemError):
    """Raised when vector store operations fail."""

    pass


class RetrievalError(RAGSystemError):
    """Raised when retrieval operations fail."""

    pass


class EmbeddingError(RAGSystemError):
    """Raised when embedding operations fail."""

    pass
