"""Unit tests for the Retriever module.

This module contains comprehensive unit tests for the Retriever class,
testing all major functionality including search operations, query
preprocessing, and result postprocessing.

Test coverage includes:
- Vector similarity search
- Hybrid search functionality
- Query preprocessing and optimization
- Result ranking and filtering
- Error conditions and edge cases
- Integration with VectorStore
"""

from unittest.mock import Mock

import pytest
from core.embedding_engine import EmbeddingEngine
from core.retriever import Retriever
from core.vector_store import VectorStore


class TestRetriever:
    """Test suite for Retriever class."""

    @pytest.fixture
    def mock_vector_store(self):
        """Create a mock VectorStore."""
        mock_store = Mock(spec=VectorStore)
        mock_store.embedding_engine = Mock(spec=EmbeddingEngine)
        return mock_store

    @pytest.fixture
    def mock_embedding_engine(self):
        """Create a mock EmbeddingEngine."""
        mock_engine = Mock(spec=EmbeddingEngine)
        mock_engine.model_name = "all-mpnet-base-v2"
        mock_engine.embedding_dimension = 768
        return mock_engine

    @pytest.fixture
    def sample_search_results(self):
        """Create sample search results for testing."""
        return [
            {
                "content": "Test content 1",
                "chunk_id": "chunk_001",
                "source_document": "test_doc.pdf",
                "chunk_type": "text",
                "metadata": {"page": 1, "author": "Test Author"},
                "page_number": 1,
                "section_title": "Test Section",
                "similarity_score": 0.85,
                "certainty": 0.85,
                "distance": 0.15,
            },
            {
                "content": "Test content 2",
                "chunk_id": "chunk_002",
                "source_document": "test_doc.pdf",
                "chunk_type": "text",
                "metadata": {"page": 2, "author": "Test Author"},
                "page_number": 2,
                "section_title": "Test Section",
                "similarity_score": 0.75,
                "certainty": 0.75,
                "distance": 0.25,
            },
        ]

    def test_retriever_initialization_with_embedding_engine(
        self, mock_vector_store, mock_embedding_engine
    ):
        """Test Retriever initialization with embedding engine."""
        retriever = Retriever(mock_vector_store, mock_embedding_engine)

        assert retriever.vector_store == mock_vector_store
        assert retriever.embedding_engine == mock_embedding_engine

    def test_retriever_initialization_without_embedding_engine(
        self, mock_vector_store, mock_embedding_engine
    ):
        """Test Retriever initialization without embedding engine."""
        mock_vector_store.embedding_engine = mock_embedding_engine

        retriever = Retriever(mock_vector_store)

        assert retriever.vector_store == mock_vector_store
        assert retriever.embedding_engine == mock_embedding_engine

    def test_retriever_initialization_with_none_vector_store(self):
        """Test Retriever initialization with None vector store."""
        with pytest.raises(ValueError, match="VectorStore cannot be None"):
            Retriever(None)

    def test_search_similar_success(self, mock_vector_store, sample_search_results):
        """Test successful vector similarity search."""
        # Setup
        mock_vector_store._search_similar_internal.return_value = sample_search_results

        retriever = Retriever(mock_vector_store)

        # Test
        results = retriever.search_similar("test query", top_k=5)

        # Assertions
        assert len(results) == 2
        assert results[0]["content"] == "Test content 1"
        assert results[0]["similarity_score"] == 0.85
        assert results[0]["retrieval_method"] == "vector_similarity"
        assert "retrieval_timestamp" in results[0]

        # Verify preprocessing was called
        mock_vector_store._search_similar_internal.assert_called_once()
        call_args = mock_vector_store._search_similar_internal.call_args
        assert call_args[1]["query"] == "test query"
        assert call_args[1]["top_k"] == 5

    def test_search_similar_empty_query(self, mock_vector_store):
        """Test vector similarity search with empty query."""
        retriever = Retriever(mock_vector_store)

        with pytest.raises(ValueError, match="Query cannot be empty"):
            retriever.search_similar("")

        with pytest.raises(ValueError, match="Query cannot be empty"):
            retriever.search_similar("   ")

    def test_search_similar_with_filters(
        self, mock_vector_store, sample_search_results
    ):
        """Test vector similarity search with filters."""
        mock_vector_store._search_similar_internal.return_value = sample_search_results
        retriever = Retriever(mock_vector_store)

        filters = {"chunk_type": "text", "author": "Test Author"}
        retriever.search_similar("test query", filters=filters)

        # Verify filters were passed
        mock_vector_store._search_similar_internal.assert_called_once()
        call_args = mock_vector_store._search_similar_internal.call_args
        assert call_args[1]["filters"] == filters

    def test_search_hybrid_success(self, mock_vector_store, sample_search_results):
        """Test successful hybrid search."""
        mock_vector_store._search_hybrid_internal.return_value = sample_search_results
        retriever = Retriever(mock_vector_store)

        results = retriever.search_hybrid("test query", alpha=0.7, top_k=3)

        assert len(results) == 2
        mock_vector_store._search_hybrid_internal.assert_called_once()
        call_args = mock_vector_store._search_hybrid_internal.call_args
        assert call_args[1]["alpha"] == 0.7
        assert call_args[1]["top_k"] == 3

    def test_search_hybrid_invalid_alpha(self, mock_vector_store):
        """Test hybrid search with invalid alpha values."""
        retriever = Retriever(mock_vector_store)

        with pytest.raises(ValueError, match="Alpha must be between 0.0 and 1.0"):
            retriever.search_hybrid("test", alpha=-0.1)

        with pytest.raises(ValueError, match="Alpha must be between 0.0 and 1.0"):
            retriever.search_hybrid("test", alpha=1.1)

    def test_search_hybrid_empty_query(self, mock_vector_store):
        """Test hybrid search with empty query."""
        retriever = Retriever(mock_vector_store)

        with pytest.raises(ValueError, match="Query cannot be empty"):
            retriever.search_hybrid("")

    def test_preprocess_query_basic(self, mock_vector_store):
        """Test basic query preprocessing."""
        retriever = Retriever(mock_vector_store)

        # Test whitespace normalization and case conversion
        processed = retriever._preprocess_query("  Test Query  ")
        assert processed == "test query"

    def test_postprocess_results(self, mock_vector_store):
        """Test result postprocessing."""
        retriever = Retriever(mock_vector_store)

        results = [
            {"similarity_score": 0.5, "content": "test 1"},
            {"similarity_score": 0.8, "content": "test 2"},
            {"similarity_score": 0.3, "content": "test 3"},
        ]

        processed = retriever._postprocess_results(results)

        # Should be sorted by similarity score (highest first)
        assert processed[0]["similarity_score"] == 0.8
        assert processed[1]["similarity_score"] == 0.5
        assert processed[2]["similarity_score"] == 0.3

        # Should have additional metadata
        for result in processed:
            assert "retrieval_method" in result
            assert "retrieval_timestamp" in result
            assert result["retrieval_method"] == "vector_similarity"

    def test_get_retrieval_stats(self, mock_vector_store, mock_embedding_engine):
        """Test retrieval statistics."""
        mock_vector_store.get_stats.return_value = {
            "total_objects": 100,
            "class_name": "Document",
        }

        retriever = Retriever(mock_vector_store, mock_embedding_engine)
        stats = retriever.get_retrieval_stats()

        assert "vector_store_stats" in stats
        assert "embedding_model" in stats
        assert "embedding_dimension" in stats
        assert "retrieval_methods" in stats
        assert stats["embedding_model"] == "all-mpnet-base-v2"
        assert stats["embedding_dimension"] == 768
        # Verify only generic retrieval methods are included
        assert "vector_similarity" in stats["retrieval_methods"]
        assert "hybrid_search" in stats["retrieval_methods"]
        assert len(stats["retrieval_methods"]) == 2

    def test_get_current_timestamp(self, mock_vector_store):
        """Test timestamp generation."""
        retriever = Retriever(mock_vector_store)

        timestamp = retriever._get_current_timestamp()
        assert isinstance(timestamp, str)
        # Should be ISO format
        assert "T" in timestamp

    def test_search_similar_error_handling(self, mock_vector_store):
        """Test error handling in search_similar."""
        mock_vector_store._search_similar_internal.side_effect = Exception(
            "Search failed"
        )
        retriever = Retriever(mock_vector_store)

        with pytest.raises(Exception, match="Search failed"):
            retriever.search_similar("test query")

    def test_search_hybrid_error_handling(self, mock_vector_store):
        """Test error handling in search_hybrid."""
        mock_vector_store._search_hybrid_internal.side_effect = Exception(
            "Hybrid search failed"
        )
        retriever = Retriever(mock_vector_store)

        with pytest.raises(Exception, match="Hybrid search failed"):
            retriever.search_hybrid("test query")

    def test_get_retrieval_stats_error_handling(self, mock_vector_store):
        """Test error handling in get_retrieval_stats."""
        mock_vector_store.get_stats.side_effect = Exception("Stats failed")
        retriever = Retriever(mock_vector_store)

        with pytest.raises(Exception, match="Stats failed"):
            retriever.get_retrieval_stats()

    def test_retriever_integration_with_vector_store(self, mock_embedding_engine):
        """Test Retriever integration with VectorStore."""
        # Create a real VectorStore mock but with controlled behavior
        mock_vector_store = Mock(spec=VectorStore)
        mock_vector_store.embedding_engine = mock_embedding_engine

        retriever = Retriever(mock_vector_store, mock_embedding_engine)

        # Test that the retriever properly uses the vector store
        assert retriever.vector_store == mock_vector_store
        assert retriever.embedding_engine == mock_embedding_engine

    def test_retriever_with_none_embedding_engine(self, mock_vector_store):
        """Test Retriever with None embedding engine uses vector store's engine."""  # noqa: E501
        mock_embedding_engine = Mock(spec=EmbeddingEngine)
        mock_vector_store.embedding_engine = mock_embedding_engine

        retriever = Retriever(mock_vector_store, None)

        assert retriever.embedding_engine == mock_embedding_engine
