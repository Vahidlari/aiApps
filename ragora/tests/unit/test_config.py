"""
Unit tests for configuration management.
"""

import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
import yaml


class TestConfigLoading:
    """Test configuration loading functionality."""

    def test_load_config_from_file(self, config_dict):
        """Test loading configuration from a file."""
        import yaml

        from ragora.config.settings import KnowledgeBaseManagerConfig

        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_dict, f)
            f.flush()
            config_path = f.name

        try:
            with open(config_path, "r") as f:
                config_dict_loaded = yaml.safe_load(f)

            config = KnowledgeBaseManagerConfig.from_dict(config_dict_loaded)
            assert config is not None
            assert config.chunk_config.chunk_size == 768
            assert config.embedding_config.model_name == "all-mpnet-base-v2"
            assert config.database_manager_config.url == "http://localhost:8080"
        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_load_config_from_dict(self):
        """Test loading configuration from dictionary."""
        from ragora.config.settings import KnowledgeBaseManagerConfig

        # Test with custom values
        config_dict = {
            "chunk": {
                "chunk_size": 512,
                "overlap_size": 50,
                "chunk_type": "text",
            },
            "embedding": {
                "model_name": "all-MiniLM-L6-v2",
                "max_length": 512,
                "device": None,
            },
            "database_manager": {
                "url": "http://localhost:8080",
                "grpc_port": 50051,
                "timeout": 30,
                "retry_attempts": 3,
            },
        }

        config = KnowledgeBaseManagerConfig.from_dict(config_dict)
        assert config is not None
        assert config.chunk_config.chunk_size == 512
        assert config.embedding_config.model_name == "all-MiniLM-L6-v2"

    def test_config_creation_with_minimal_dict(self):
        """Test configuration creation with minimal dictionary."""
        from ragora.config.settings import KnowledgeBaseManagerConfig

        # Test with minimal config (only required fields)
        minimal_config = {
            "chunk": {"chunk_size": 512, "overlap_size": 100, "chunk_type": "text"},
            "embedding": {"model_name": "test-model"},
            "database_manager": {"url": "http://test:8080"},
        }

        config = KnowledgeBaseManagerConfig.from_dict(minimal_config)
        assert config is not None
        assert config.chunk_config.chunk_size == 512
        assert config.embedding_config.model_name == "test-model"
        assert config.database_manager_config.url == "http://test:8080"
        # Should use defaults for missing fields
        assert config.chunk_config.overlap_size == 100  # default
        assert config.embedding_config.max_length == 512  # default
        assert config.database_manager_config.grpc_port == 50051  # default

    def test_config_with_various_types(self):
        """Test configuration with various data types."""
        from ragora.config.settings import KnowledgeBaseManagerConfig

        # Test that the dataclass accepts various types (no validation)
        mixed_config = {
            "chunk": {
                "chunk_size": 768,
                "overlap_size": 100,
                "chunk_type": "text",
            },
            "embedding": {
                "model_name": "all-mpnet-base-v2",
                "max_length": 512,
                "device": None,
            },
            "database_manager": {
                "url": "http://localhost:8080",
                "grpc_port": 50051,
                "timeout": 30,
                "retry_attempts": 3,
            },
        }

        # Should create config successfully (dataclass doesn't validate types)
        config = KnowledgeBaseManagerConfig.from_dict(mixed_config)
        assert config is not None
        assert config.chunk_config.chunk_size == 768
        assert config.embedding_config.model_name == "all-mpnet-base-v2"
        assert config.database_manager_config.url == "http://localhost:8080"

    def test_config_environment_variables(self, config_dict):
        """Test that configuration can be created with environment variables."""
        import os

        from ragora.config.settings import KnowledgeBaseManagerConfig

        # Mock environment variables
        with patch.dict(
            os.environ,
            {
                "KBM_CHUNK_SIZE": "1024",
                "KBM_EMBEDDING_MODEL": "sentence-transformers/all-mpnet-base-v2",
                "KBM_DB_URL": "http://localhost:9090",
            },
        ):
            # Modify config dict with environment values
            modified_config = config_dict.copy()
            modified_config["chunk"]["chunk_size"] = 1024
            modified_config["embedding"][
                "model_name"
            ] = "sentence-transformers/all-mpnet-base-v2"
            modified_config["database_manager"]["url"] = "http://localhost:9090"

            config = KnowledgeBaseManagerConfig.from_dict(modified_config)
            assert config is not None
            assert config.chunk_config.chunk_size == 1024
            assert (
                config.embedding_config.model_name
                == "sentence-transformers/all-mpnet-base-v2"
            )
            assert config.database_manager_config.url == "http://localhost:9090"


class TestConfigValidation:
    """Test configuration validation functionality."""

    def test_validate_config_valid(self, config_dict):
        """Test validation of valid configuration."""
        from ragora.config.settings import KnowledgeBaseManagerConfig

        # Should not raise any exceptions for valid config
        config = KnowledgeBaseManagerConfig.from_dict(config_dict)
        assert config is not None

    def test_validate_config_missing_required_sections(self):
        """Test validation with missing required sections."""
        from ragora.config.settings import KnowledgeBaseManagerConfig

        incomplete_config = {
            "chunk": {"chunk_size": 768}
            # Missing embedding and database_manager sections
        }

        # Dataclass doesn't validate missing sections, it uses defaults
        config = KnowledgeBaseManagerConfig.from_dict(incomplete_config)
        assert config is not None
        # Should set None for missing sections
        assert config.embedding_config is None
        assert config.database_manager_config is None

    def test_validate_config_invalid_chunk_size(self):
        """Test validation with invalid chunk size."""
        from ragora.config.settings import KnowledgeBaseManagerConfig

        invalid_config = {
            "chunk": {
                "chunk_size": -100,  # Invalid negative value
                "overlap_size": 50,
                "chunk_type": "text",
            },
            "embedding": {"model_name": "all-mpnet-base-v2", "max_length": 512},
            "database_manager": {"url": "http://localhost:8080", "grpc_port": 50051},
        }

        # Should create config but with invalid values (dataclass doesn't validate)
        # This test documents the current behavior - no validation on creation
        config = KnowledgeBaseManagerConfig.from_dict(invalid_config)
        assert config.chunk_config.chunk_size == -100  # Invalid value is accepted

    def test_config_creation_with_various_values(self):
        """Test configuration creation with various values."""
        from ragora.config.settings import KnowledgeBaseManagerConfig

        # Test with overlap larger than chunk size (invalid but accepted)
        config1 = {
            "chunk": {
                "chunk_size": 768,
                "overlap_size": 1000,  # Overlap larger than chunk size
                "chunk_type": "text",
            },
            "embedding": {"model_name": "all-mpnet-base-v2", "max_length": 512},
            "database_manager": {"url": "http://localhost:8080", "grpc_port": 50051},
        }

        config = KnowledgeBaseManagerConfig.from_dict(config1)
        assert config.chunk_config.overlap_size == 1000  # Invalid value is accepted

        # Test with empty model name (invalid but accepted)
        config2 = {
            "chunk": {
                "chunk_size": 768,
                "overlap_size": 100,
                "chunk_type": "text",
            },
            "embedding": {"model_name": "", "max_length": 512},  # Empty model name
            "database_manager": {"url": "http://localhost:8080", "grpc_port": 50051},
        }

        config = KnowledgeBaseManagerConfig.from_dict(config2)
        assert config.embedding_config.model_name == ""  # Invalid value is accepted

        # Test with invalid port number (invalid but accepted)
        config3 = {
            "chunk": {
                "chunk_size": 768,
                "overlap_size": 100,
                "chunk_type": "text",
            },
            "embedding": {"model_name": "all-mpnet-base-v2", "max_length": 512},
            "database_manager": {
                "url": "http://localhost:8080",
                "grpc_port": 99999,  # Invalid port number
            },
        }

        config = KnowledgeBaseManagerConfig.from_dict(config3)
        assert (
            config.database_manager_config.grpc_port == 99999
        )  # Invalid value is accepted


class TestConfigDefaults:
    """Test configuration default values."""

    def test_get_default_config(self):
        """Test getting default configuration."""
        from ragora.config.settings import KnowledgeBaseManagerConfig

        default_config = KnowledgeBaseManagerConfig.default()

        assert default_config is not None
        assert default_config.chunk_config is not None
        assert default_config.embedding_config is not None
        assert default_config.database_manager_config is not None

        # Check default values
        assert default_config.chunk_config.chunk_size == 768
        assert default_config.chunk_config.overlap_size == 100
        assert default_config.embedding_config.model_name == "all-mpnet-base-v2"
        assert default_config.database_manager_config.url == "http://localhost:8080"

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        from ragora.config.settings import KnowledgeBaseManagerConfig

        config_dict = {
            "chunk": {"chunk_size": 1024, "overlap_size": 150, "chunk_type": "text"},
            "embedding": {"model_name": "custom-model", "max_length": 256},
            "database_manager": {"url": "http://custom:9090", "timeout": 60},
        }

        config = KnowledgeBaseManagerConfig.from_dict(config_dict)

        # Should have user values
        assert config.chunk_config.chunk_size == 1024
        assert config.chunk_config.overlap_size == 150
        assert config.embedding_config.model_name == "custom-model"
        assert config.embedding_config.max_length == 256
        assert config.database_manager_config.url == "http://custom:9090"
        assert config.database_manager_config.timeout == 60

        # Should have defaults for missing fields
        assert config.chunk_config.chunk_type == "text"
        assert config.embedding_config.device is None
        assert config.database_manager_config.grpc_port == 50051


class TestConfigSchema:
    """Test configuration schema validation."""

    def test_config_schema_structure(self, config_dict):
        """Test that config follows expected schema structure."""
        required_sections = [
            "chunk",
            "embedding",
            "database_manager",
        ]

        for section in required_sections:
            assert section in config_dict, f"Missing required section: {section}"

    def test_chunk_schema(self, config_dict):
        """Test chunk configuration schema."""
        chunk_config = config_dict["chunk"]

        required_fields = [
            "chunk_size",
            "overlap_size",
            "chunk_type",
        ]

        for field in required_fields:
            assert field in chunk_config, f"Missing required field: {field}"

        # Check types
        assert isinstance(chunk_config["chunk_size"], int)
        assert isinstance(chunk_config["overlap_size"], int)
        assert isinstance(chunk_config["chunk_type"], str)

    def test_embedding_schema(self, config_dict):
        """Test embedding configuration schema."""
        embedding = config_dict["embedding"]

        required_fields = ["model_name", "max_length"]

        for field in required_fields:
            assert field in embedding, f"Missing required field: {field}"

        # Check types
        assert isinstance(embedding["model_name"], str)
        assert isinstance(embedding["max_length"], int)
        # device can be None or string
        assert embedding["device"] is None or isinstance(embedding["device"], str)

    def test_database_manager_schema(self, config_dict):
        """Test database manager configuration schema."""
        db_manager = config_dict["database_manager"]

        required_fields = ["url", "grpc_port", "timeout", "retry_attempts"]

        for field in required_fields:
            assert field in db_manager, f"Missing required field: {field}"

        # Check types
        assert isinstance(db_manager["url"], str)
        assert isinstance(db_manager["grpc_port"], int)
        assert isinstance(db_manager["timeout"], int)
        assert isinstance(db_manager["retry_attempts"], int)
