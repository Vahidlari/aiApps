"""Configuration classes for the RAG system."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ChunkConfig:
    """Configuration for document chunking."""

    chunk_size: int = 768
    overlap: int = 100
    strategy: str = "adaptive_fixed_size"


@dataclass
class EmbeddingConfig:
    """Configuration for embedding engine."""

    model_name: str = "all-mpnet-base-v2"
    device: Optional[str] = None
    max_length: int = 512


@dataclass
class VectorStoreConfig:
    """Configuration for vector store."""

    url: str = "http://localhost:8080"
    class_name: str = "Document"
    timeout: int = 30


@dataclass
class RAGConfig:
    """Main configuration for RAG system."""

    chunk_config: ChunkConfig
    embedding_config: EmbeddingConfig
    vector_store_config: VectorStoreConfig

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "RAGConfig":
        """Create config from dictionary."""
        return cls(
            chunk_config=ChunkConfig(**config_dict.get("chunk", {})),
            embedding_config=EmbeddingConfig(**config_dict.get("embedding", {})),
            vector_store_config=VectorStoreConfig(
                **config_dict.get("vector_store", {})
            ),
        )

    @classmethod
    def default(cls) -> "RAGConfig":
        """Create default configuration."""
        return cls(
            chunk_config=ChunkConfig(),
            embedding_config=EmbeddingConfig(),
            vector_store_config=VectorStoreConfig(),
        )
