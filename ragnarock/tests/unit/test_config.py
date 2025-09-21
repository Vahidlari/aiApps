"""
Unit tests for configuration management.
"""

import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
import yaml


@pytest.mark.skip(reason="Config module not yet implemented")
class TestConfigLoading:
    """Test configuration loading functionality."""

    def test_load_config_from_file(self, config_dict):
        """Test loading configuration from a file."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_dict, f)
            f.flush()
            config_path = f.name

        try:
            config = load_config(config_path)
            assert config is not None
            assert config["document_processing"]["chunk_size"] == 768
            assert config["embedding"]["model"] == "all-mpnet-base-v2"
            assert config["vector_database"]["type"] == "weaviate"
        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_load_config_with_default_path(self):
        """Test loading configuration with default path."""
        # Mock the default config file
        default_config_content = """
document_processing:
  chunk_size: 512
  overlap: 50
  preserve_equations: true

embedding:
  model: "all-MiniLM-L6-v2"
  batch_size: 16

vector_database:
  type: "weaviate"
  url: "http://localhost:8080"
"""

        with patch("builtins.open", mock_open(read_data=default_config_content)):
            with patch("pathlib.Path.exists", return_value=True):
                config = load_config()
                assert config is not None
                assert config["document_processing"]["chunk_size"] == 512
                assert config["embedding"]["model"] == "all-MiniLM-L6-v2"

    def test_load_config_file_not_found(self):
        """Test loading configuration when file doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            config = load_config("nonexistent.yaml")
            assert config is None

    def test_load_config_invalid_yaml(self):
        """Test loading configuration with invalid YAML."""
        invalid_yaml_content = """
document_processing:
  chunk_size: 768
  overlap: 100
  preserve_equations: true
invalid_yaml: [unclosed list
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(invalid_yaml_content)
            f.flush()
            config_path = f.name

        try:
            config = load_config(config_path)
            assert config is None
        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_load_config_with_environment_overrides(self, config_dict):
        """Test loading configuration with environment variable overrides."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_dict, f)
            f.flush()
            config_path = f.name

        try:
            # Mock environment variables
            with patch.dict(
                "os.environ",
                {
                    "RAG_CHUNK_SIZE": "1024",
                    "RAG_EMBEDDING_MODEL": "sentence-transformers/all-mpnet-base-v2",
                    "RAG_VECTOR_DB_URL": "http://localhost:9090",
                },
            ):
                config = load_config(config_path, use_env=True)
                assert config is not None
                assert config["document_processing"]["chunk_size"] == 1024
                assert (
                    config["embedding"]["model"]
                    == "sentence-transformers/all-mpnet-base-v2"
                )
                assert config["vector_database"]["url"] == "http://localhost:9090"
        finally:
            Path(config_path).unlink(missing_ok=True)


@pytest.mark.skip(reason="Config module not yet implemented")
class TestConfigValidation:
    """Test configuration validation functionality."""

    def test_validate_config_valid(self, config_dict):
        """Test validation of valid configuration."""
        is_valid, errors = validate_config(config_dict)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_config_missing_required_sections(self):
        """Test validation with missing required sections."""
        incomplete_config = {
            "document_processing": {"chunk_size": 768}
            # Missing embedding and vector_database sections
        }

        is_valid, errors = validate_config(incomplete_config)
        assert is_valid is False
        assert len(errors) > 0
        assert any("embedding" in error for error in errors)
        assert any("vector_database" in error for error in errors)

    def test_validate_config_invalid_chunk_size(self):
        """Test validation with invalid chunk size."""
        invalid_config = {
            "document_processing": {
                "chunk_size": -100,  # Invalid negative value
                "overlap": 50,
                "preserve_equations": True,
            },
            "embedding": {"model": "all-mpnet-base-v2", "batch_size": 32},
            "vector_database": {"type": "weaviate", "url": "http://localhost:8080"},
        }

        is_valid, errors = validate_config(invalid_config)
        assert is_valid is False
        assert any("chunk_size" in error for error in errors)

    def test_validate_config_invalid_overlap(self):
        """Test validation with invalid overlap value."""
        invalid_config = {
            "document_processing": {
                "chunk_size": 768,
                "overlap": 1000,  # Overlap larger than chunk size
                "preserve_equations": True,
            },
            "embedding": {"model": "all-mpnet-base-v2", "batch_size": 32},
            "vector_database": {"type": "weaviate", "url": "http://localhost:8080"},
        }

        is_valid, errors = validate_config(invalid_config)
        assert is_valid is False
        assert any("overlap" in error for error in errors)

    def test_validate_config_invalid_embedding_model(self):
        """Test validation with invalid embedding model."""
        invalid_config = {
            "document_processing": {
                "chunk_size": 768,
                "overlap": 100,
                "preserve_equations": True,
            },
            "embedding": {"model": "", "batch_size": 32},  # Empty model name
            "vector_database": {"type": "weaviate", "url": "http://localhost:8080"},
        }

        is_valid, errors = validate_config(invalid_config)
        assert is_valid is False
        assert any("embedding" in error for error in errors)

    def test_validate_config_invalid_vector_db_type(self):
        """Test validation with invalid vector database type."""
        invalid_config = {
            "document_processing": {
                "chunk_size": 768,
                "overlap": 100,
                "preserve_equations": True,
            },
            "embedding": {"model": "all-mpnet-base-v2", "batch_size": 32},
            "vector_database": {
                "type": "invalid_db",  # Unsupported database type
                "url": "http://localhost:8080",
            },
        }

        is_valid, errors = validate_config(invalid_config)
        assert is_valid is False
        assert any("vector_database" in error for error in errors)

    def test_validate_config_invalid_url(self):
        """Test validation with invalid URL."""
        invalid_config = {
            "document_processing": {
                "chunk_size": 768,
                "overlap": 100,
                "preserve_equations": True,
            },
            "embedding": {"model": "all-mpnet-base-v2", "batch_size": 32},
            "vector_database": {
                "type": "weaviate",
                "url": "invalid-url",  # Invalid URL format
            },
        }

        is_valid, errors = validate_config(invalid_config)
        assert is_valid is False
        assert any("url" in error for error in errors)


@pytest.mark.skip(reason="Config module not yet implemented")
class TestConfigDefaults:
    """Test configuration default values."""

    def test_get_default_config(self):
        """Test getting default configuration."""
        default_config = get_default_config()

        assert default_config is not None
        assert "document_processing" in default_config
        assert "embedding" in default_config
        assert "vector_database" in default_config

        # Check default values
        assert default_config["document_processing"]["chunk_size"] == 768
        assert default_config["document_processing"]["overlap"] == 100
        assert default_config["embedding"]["model"] == "all-mpnet-base-v2"
        assert default_config["vector_database"]["type"] == "weaviate"

    def test_merge_config_with_defaults(self):
        """Test merging user config with defaults."""
        user_config = {
            "document_processing": {"chunk_size": 1024},  # Override default
            "embedding": {"batch_size": 64},  # Override default
            # Missing vector_database section
        }

        merged_config = merge_config_with_defaults(user_config)

        # Should have user overrides
        assert merged_config["document_processing"]["chunk_size"] == 1024
        assert merged_config["embedding"]["batch_size"] == 64

        # Should have defaults for missing sections
        assert merged_config["vector_database"]["type"] == "weaviate"
        assert merged_config["vector_database"]["url"] == "http://localhost:8080"

        # Should have defaults for missing fields
        assert merged_config["document_processing"]["overlap"] == 100
        assert merged_config["embedding"]["model"] == "all-mpnet-base-v2"


@pytest.mark.skip(reason="Config module not yet implemented")
class TestConfigSchema:
    """Test configuration schema validation."""

    def test_config_schema_structure(self, config_dict):
        """Test that config follows expected schema structure."""
        required_sections = [
            "document_processing",
            "embedding",
            "vector_database",
            "retrieval",
            "generation",
            "prompts",
            "logging",
            "performance",
        ]

        for section in required_sections:
            assert section in config_dict, f"Missing required section: {section}"

    def test_document_processing_schema(self, config_dict):
        """Test document processing configuration schema."""
        doc_proc = config_dict["document_processing"]

        required_fields = [
            "chunk_size",
            "overlap",
            "preserve_equations",
            "remove_latex_commands",
            "separate_citations",
        ]

        for field in required_fields:
            assert field in doc_proc, f"Missing required field: {field}"

        # Check types
        assert isinstance(doc_proc["chunk_size"], int)
        assert isinstance(doc_proc["overlap"], int)
        assert isinstance(doc_proc["preserve_equations"], bool)
        assert isinstance(doc_proc["remove_latex_commands"], bool)
        assert isinstance(doc_proc["separate_citations"], bool)

    def test_embedding_schema(self, config_dict):
        """Test embedding configuration schema."""
        embedding = config_dict["embedding"]

        required_fields = ["model", "batch_size", "device"]

        for field in required_fields:
            assert field in embedding, f"Missing required field: {field}"

        # Check types
        assert isinstance(embedding["model"], str)
        assert isinstance(embedding["batch_size"], int)
        assert isinstance(embedding["device"], str)

    def test_vector_database_schema(self, config_dict):
        """Test vector database configuration schema."""
        vector_db = config_dict["vector_database"]

        required_fields = ["type", "url"]

        for field in required_fields:
            assert field in vector_db, f"Missing required field: {field}"

        # Check types
        assert isinstance(vector_db["type"], str)
        assert isinstance(vector_db["url"], str)

        # Check valid database types
        valid_types = ["weaviate", "chroma", "faiss", "pinecone"]
        assert vector_db["type"] in valid_types


# Helper functions for testing (these would be implemented in the actual config module)
@pytest.mark.skip(reason="Config module not yet implemented")
def get_default_config():
    """Get default configuration."""
    return {
        "document_processing": {
            "chunk_size": 768,
            "overlap": 100,
            "preserve_equations": True,
            "remove_latex_commands": True,
            "separate_citations": True,
        },
        "embedding": {"model": "all-mpnet-base-v2", "batch_size": 32, "device": "auto"},
        "vector_database": {"type": "weaviate", "url": "http://localhost:8080"},
        "retrieval": {"search_type": "hybrid", "top_k": 5, "score_threshold": 0.7},
        "generation": {
            "model": "mistral:7b",
            "provider": "ollama",
            "temperature": 0.7,
            "max_tokens": 1000,
        },
        "prompts": {
            "rag_template": "You are a helpful assistant...",
            "citation_template": "Based on the provided context...",
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "performance": {"max_workers": 4, "cache_size": 1000, "enable_caching": True},
    }


@pytest.mark.skip(reason="Config module not yet implemented")
def merge_config_with_defaults(user_config):
    """Merge user configuration with defaults."""
    default_config = get_default_config()
    merged = default_config.copy()

    def deep_merge(default, user):
        for key, value in user.items():
            if (
                key in default
                and isinstance(default[key], dict)
                and isinstance(value, dict)
            ):
                deep_merge(default[key], value)
            else:
                default[key] = value

    deep_merge(merged, user_config)
    return merged
