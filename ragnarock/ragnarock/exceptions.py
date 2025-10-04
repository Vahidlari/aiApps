"""Custom exceptions for the knowledge base manager system."""


class KnowledgeBaseManagerError(Exception):
    """Base exception for knowledge base manager errors."""

    pass


class ConfigurationError(KnowledgeBaseManagerError):
    """Raised when there's a configuration error."""

    pass


class DocumentProcessingError(KnowledgeBaseManagerError):
    """Raised when document processing fails."""

    pass


class VectorStoreError(KnowledgeBaseManagerError):
    """Raised when vector store operations fail."""

    pass


class RetrievalError(KnowledgeBaseManagerError):
    """Raised when retrieval operations fail."""

    pass


class EmbeddingError(KnowledgeBaseManagerError):
    """Raised when embedding operations fail."""

    pass
