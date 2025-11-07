"""Dataclasses that capture Ragora configuration."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ChunkConfig:
    """Chunking behaviour for document ingestion.

    Attributes:
        chunk_size: Target token length per chunk.
        overlap_size: Token overlap between sequential chunks.
        chunk_type: Friendly label used downstream for metadata.
    """

    chunk_size: int = 768
    overlap_size: int = 100
    chunk_type: str = "document"


@dataclass
class EmbeddingConfig:
    """Sentence-transformer settings for semantic retrieval.

    Attributes:
        model_name: Hugging Face model identifier.
        device: Explicit torch device string (``\"cpu\"``, ``\"cuda\"``); ``None`` auto-selects.
        max_length: Maximum tokens per forward pass.
    """

    model_name: str = "all-mpnet-base-v2"
    device: Optional[str] = None
    max_length: int = 512


@dataclass
class DatabaseManagerConfig:
    """Connection properties for the Weaviate backend.

    Attributes:
        url: HTTP endpoint for Weaviate.
        grpc_port: Optional gRPC port.
        timeout: Request timeout in seconds.
        retry_attempts: Automatic retry count for transient failures.
    """

    url: str = "http://localhost:8080"
    grpc_port: int = 50051
    timeout: int = 30
    retry_attempts: int = 3


@dataclass
class KnowledgeBaseManagerConfig:
    """Aggregates all subsystems used by :class:`KnowledgeBaseManager`."""

    chunk_config: Optional[ChunkConfig] = None
    embedding_config: Optional[EmbeddingConfig] = None
    database_manager_config: Optional[DatabaseManagerConfig] = None

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "KnowledgeBaseManagerConfig":
        """Create a configuration from nested dictionaries.

        Args:
            config_dict: Dictionary matching the dataclass schema
                (the keys ``chunk``, ``embedding``, ``database_manager`` are recognised).

        Returns:
            KnowledgeBaseManagerConfig: Parsed configuration instance.

        Examples:
            ```python
            cfg = KnowledgeBaseManagerConfig.from_dict(
                {
                    "chunk": {"chunk_size": 512, "overlap_size": 64},
                    "embedding": {"model_name": "multi-qa-MiniLM-L6-v2"},
                }
            )
            ```
        """
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
        """Create a configuration with Ragora defaults.

        Returns:
            KnowledgeBaseManagerConfig: Configuration using standard values.

        Examples:
            ```python
            cfg = KnowledgeBaseManagerConfig.default()
            ```
        """
        return cls(
            chunk_config=ChunkConfig(),
            embedding_config=EmbeddingConfig(),
            database_manager_config=DatabaseManagerConfig(),
        )
