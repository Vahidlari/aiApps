"""Configuration classes for the RAG system."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ChunkConfig:
    """Configuration for document chunking."""

    chunk_size: int = 768  # size of the chunk
    overlap_size: int = 100  # overlap size of the chunk
    chunk_type: str = "document"  # type of the chunk


@dataclass
class EmbeddingConfig:
    """Configuration for embedding engine."""

    model_name: str = "all-mpnet-base-v2"  # model to use for the embedding
    device: Optional[str] = None  # device to use for the embedding
    max_length: int = 512  # max length of the embedding


@dataclass
class DatabaseManagerConfig:
    """Configuration for database manager."""

    url: str = "http://localhost:8080"  # url of the database manager
    grpc_port: int = 50051  # grpc port of the database manager
    timeout: int = 30  # timeout for the database manager
    retry_attempts: int = 3  # retry attempts for the database manager


@dataclass
class KnowledgeBaseManagerConfig:
    """Main configuration for Knowledge Base Manager."""

    chunk_config: Optional[ChunkConfig] = None
    embedding_config: Optional[EmbeddingConfig] = None
    database_manager_config: Optional[DatabaseManagerConfig] = None

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "KnowledgeBaseManagerConfig":
        """Create config from dictionary."""
        return cls(
            chunk_config=(
                ChunkConfig(**config_dict.get("chunk", {}))
                if config_dict.get("chunk")
                else None
            ),
            embedding_config=(
                EmbeddingConfig(**config_dict.get("embedding", {}))
                if config_dict.get("embedding")
                else None
            ),
            database_manager_config=(
                DatabaseManagerConfig(**config_dict.get("database_manager", {}))
                if config_dict.get("database_manager")
                else None
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
