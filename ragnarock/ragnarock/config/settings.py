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
class DatabaseManagerConfig:
    """Configuration for database manager."""

    url: str = "http://localhost:8080"
    grpc_port: int = 50051
    timeout: int = 30
    retry_attempts: int = 3


@dataclass
class KnowledgeBaseManagerConfig:
    """Main configuration for Knowledge Base Manager."""

    chunk_config: ChunkConfig
    embedding_config: EmbeddingConfig
    database_manager_config: DatabaseManagerConfig

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "KnowledgeBaseManagerConfig":
        """Create config from dictionary."""
        return cls(
            chunk_config=ChunkConfig(**config_dict.get("chunk", {})),
            embedding_config=EmbeddingConfig(**config_dict.get("embedding", {})),
            database_manager_config=DatabaseManagerConfig(
                **config_dict.get("database_manager", {})
            ),
        )

    @classmethod
    def default(cls) -> "KnowledgeBaseManagerConfig":
        """Create default configuration."""
        return cls(
            chunk_config=ChunkConfig(),
            embedding_config=EmbeddingConfig(),
            database_manager_config=DatabaseManagerConfig(),
        )
