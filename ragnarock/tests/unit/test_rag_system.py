"""Unit tests for the RAGSystem module.

This module contains comprehensive unit tests for the RAGSystem class,
testing the orchestration of all components and the unified interface.

Test coverage includes:
- System initialization and configuration
- Document processing pipeline
- Unified query interface
- Component integration
- Error handling and edge cases
- System statistics and monitoring
- Context manager functionality
"""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest

from ragnarock import (
    DataChunk,
    DataChunker,
    DocumentPreprocessor,
    EmbeddingEngine,
    RAGSystem,
    Retriever,
    VectorStore,
)


class TestRAGSystem:
    """Test suite for RAGSystem class."""

    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing."""
        mock_vector_store = Mock(spec=VectorStore)
        mock_retriever = Mock(spec=Retriever)
        mock_embedding_engine = Mock(spec=EmbeddingEngine)
        mock_document_preprocessor = Mock(spec=DocumentPreprocessor)
        mock_data_chunker = Mock(spec=DataChunker)

        return {
            "vector_store": mock_vector_store,
            "retriever": mock_retriever,
            "embedding_engine": mock_embedding_engine,
            "document_preprocessor": mock_document_preprocessor,
            "data_chunker": mock_data_chunker,
        }

    @pytest.fixture
    def sample_chunks(self):
        """Create sample DataChunk objects for testing."""
        from ragnarock.core.data_chunker import ChunkMetadata

        return [
            DataChunk(
                text="Test content 1",
                start_idx=0,
                end_idx=15,
                metadata=ChunkMetadata(
                    chunk_id=1,
                    chunk_size=15,
                    total_chunks=2,
                    source_document="test.tex",
                    page_number=1,
                    chunk_type="text",
                ),
                chunk_id="test_001",
                source_document="test.tex",
                chunk_type="text",
            ),
            DataChunk(
                text="Test content 2",
                start_idx=16,
                end_idx=31,
                metadata=ChunkMetadata(
                    chunk_id=2,
                    chunk_size=15,
                    total_chunks=2,
                    source_document="test.tex",
                    page_number=2,
                    chunk_type="equation",
                ),
                chunk_id="test_002",
                source_document="test.tex",
                chunk_type="equation",
            ),
        ]

    @pytest.fixture
    def sample_search_results(self):
        """Create sample search results for testing."""
        return [
            {
                "content": "Test content 1",
                "chunk_id": "test_001",
                "source_document": "test.tex",
                "chunk_type": "text",
                "metadata": {"page": 1, "author": "Test Author"},
                "similarity_score": 0.85,
            },
            {
                "content": "Test content 2",
                "chunk_id": "test_002",
                "source_document": "test.tex",
                "chunk_type": "equation",
                "metadata": {"page": 2, "author": "Test Author"},
                "similarity_score": 0.75,
            },
        ]

    @patch("ragnarock.ragnarock.core.rag_system.EmbeddingEngine")
    @patch("ragnarock.ragnarock.core.rag_system.VectorStore")
    @patch("ragnarock.ragnarock.core.rag_system.Retriever")
    @patch("ragnarock.ragnarock.core.rag_system.DocumentPreprocessor")
    @patch("ragnarock.ragnarock.core.rag_system.DataChunker")
    def test_rag_system_initialization_success(
        self,
        mock_data_chunker,
        mock_document_preprocessor,
        mock_retriever,
        mock_vector_store,
        mock_embedding_engine,
    ):
        """Test successful RAGSystem initialization."""
        # Setup mocks
        mock_embedding_engine.return_value = Mock()
        mock_vector_store.return_value = Mock()
        mock_retriever.return_value = Mock()
        mock_document_preprocessor.return_value = Mock()
        mock_data_chunker.return_value = Mock()

        # Test
        rag = RAGSystem(
            weaviate_url="http://localhost:8080",
            class_name="TestDocument",
            embedding_model="all-mpnet-base-v2",
            chunk_size=512,
            chunk_overlap=50,
        )

        # Assertions
        assert rag.is_initialized is True
        mock_embedding_engine.assert_called_once_with(model_name="all-mpnet-base-v2")
        mock_vector_store.assert_called_once()
        mock_retriever.assert_called_once()
        mock_document_preprocessor.assert_called_once()
        mock_data_chunker.assert_called_once_with(chunk_size=512, overlap_size=50)

    @patch("ragnarock.ragnarock.core.rag_system.EmbeddingEngine")
    def test_rag_system_initialization_failure(self, mock_embedding_engine):
        """Test RAGSystem initialization failure."""
        mock_embedding_engine.side_effect = Exception("Embedding engine failed")

        with pytest.raises(Exception, match="Embedding engine failed"):
            RAGSystem()

    def test_process_document_success(self, mock_components, sample_chunks):
        """Test successful document processing."""
        # Setup
        mock_components["document_preprocessor"].preprocess_document.return_value = (
            sample_chunks
        )
        mock_components["vector_store"].store_chunks.return_value = ["uuid1", "uuid2"]

        # Create RAG system with mocked components
        rag = RAGSystem.__new__(RAGSystem)
        rag.is_initialized = True
        rag.document_preprocessor = mock_components["document_preprocessor"]
        rag.vector_store = mock_components["vector_store"]
        rag.logger = Mock()

        # Test
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", delete=False) as f:
            f.write(
                "\\documentclass{article}\\begin{document}Test content\\end{document}"
            )
            temp_path = f.name

        try:
            result = rag.process_document(temp_path)

            # Assertions
            assert result == ["uuid1", "uuid2"]
            mock_components[
                "document_preprocessor"
            ].preprocess_document.assert_called_once_with(temp_path, "latex")
            mock_components["vector_store"].store_chunks.assert_called_once_with(
                sample_chunks
            )
        finally:
            os.unlink(temp_path)

    def test_process_document_not_initialized(self):
        """Test document processing when system not initialized."""
        rag = RAGSystem.__new__(RAGSystem)
        rag.is_initialized = False

        with pytest.raises(RuntimeError, match="RAG system not initialized"):
            rag.process_document("test.tex")

    def test_process_document_file_not_found(self, mock_components):
        """Test document processing with non-existent file."""
        mock_components["document_preprocessor"].preprocess_document.side_effect = (
            FileNotFoundError("File not found")
        )

        rag = RAGSystem.__new__(RAGSystem)
        rag.is_initialized = True
        rag.document_preprocessor = mock_components["document_preprocessor"]
        rag.data_chunker = mock_components["data_chunker"]
        rag.vector_store = mock_components["vector_store"]
        rag.logger = Mock()

        with pytest.raises(FileNotFoundError, match="File not found"):
            rag.process_document("nonexistent.tex")

    def test_query_similar_success(self, mock_components, sample_search_results):
        """Test successful query with similar search."""
        mock_components["retriever"].search_similar.return_value = sample_search_results

        rag = RAGSystem.__new__(RAGSystem)
        rag.is_initialized = True
        rag.retriever = mock_components["retriever"]
        rag.logger = Mock()

        # Test
        result = rag.query("What is the test content?", search_type="similar", top_k=5)

        # Assertions
        assert result["question"] == "What is the test content?"
        assert result["search_type"] == "similar"
        assert result["num_chunks"] == 2
        assert result["retrieved_chunks"] == sample_search_results
        assert "test.tex" in result["chunk_sources"]
        assert "text" in result["chunk_types"]
        assert "equation" in result["chunk_types"]
        assert result["avg_similarity"] == 0.8  # (0.85 + 0.75) / 2
        assert result["max_similarity"] == 0.85

        mock_components["retriever"].search_similar.assert_called_once_with(
            "What is the test content?", top_k=5
        )

    def test_query_hybrid_success(self, mock_components, sample_search_results):
        """Test successful query with hybrid search."""
        mock_components["retriever"].search_hybrid.return_value = sample_search_results

        rag = RAGSystem.__new__(RAGSystem)
        rag.is_initialized = True
        rag.retriever = mock_components["retriever"]
        rag.logger = Mock()

        # Test
        result = rag.query("What is the test content?", search_type="hybrid", top_k=3)

        # Assertions
        assert result["search_type"] == "hybrid"
        mock_components["retriever"].search_hybrid.assert_called_once_with(
            "What is the test content?", top_k=3
        )

    def test_query_invalid_search_type(self, mock_components):
        """Test query with invalid search type."""
        rag = RAGSystem.__new__(RAGSystem)
        rag.is_initialized = True
        rag.retriever = mock_components["retriever"]
        rag.logger = Mock()

        with pytest.raises(ValueError, match="Invalid search type: invalid"):
            rag.query("test", search_type="invalid")

    def test_query_empty_question(self, mock_components):
        """Test query with empty question."""
        rag = RAGSystem.__new__(RAGSystem)
        rag.is_initialized = True
        rag.retriever = mock_components["retriever"]
        rag.logger = Mock()

        with pytest.raises(ValueError, match="Question cannot be empty"):
            rag.query("")

    def test_query_not_initialized(self):
        """Test query when system not initialized."""
        rag = RAGSystem.__new__(RAGSystem)
        rag.is_initialized = False

        with pytest.raises(RuntimeError, match="RAG system not initialized"):
            rag.query("test question")

    def test_search_similar_delegation(self, mock_components, sample_search_results):
        """Test that search_similar delegates to retriever."""
        mock_components["retriever"].search_similar.return_value = sample_search_results

        rag = RAGSystem.__new__(RAGSystem)
        rag.is_initialized = True
        rag.retriever = mock_components["retriever"]

        # Test
        result = rag.search_similar(
            "test query", top_k=5, filters={"chunk_type": "text"}
        )

        # Assertions
        assert result == sample_search_results
        mock_components["retriever"].search_similar.assert_called_once_with(
            "test query", top_k=5, filters={"chunk_type": "text"}
        )

    def test_search_hybrid_delegation(self, mock_components, sample_search_results):
        """Test that search_hybrid delegates to retriever."""
        mock_components["retriever"].search_hybrid.return_value = sample_search_results

        rag = RAGSystem.__new__(RAGSystem)
        rag.is_initialized = True
        rag.retriever = mock_components["retriever"]

        # Test
        result = rag.search_hybrid(
            "test query", alpha=0.7, top_k=3, filters={"chunk_type": "text"}
        )

        # Assertions
        assert result == sample_search_results
        mock_components["retriever"].search_hybrid.assert_called_once_with(
            "test query", alpha=0.7, top_k=3, filters={"chunk_type": "text"}
        )

    def test_get_chunk_delegation(self, mock_components):
        """Test that get_chunk delegates to vector_store."""
        mock_chunk_data = {"chunk_id": "test_001", "content": "test content"}
        mock_components["vector_store"].get_chunk_by_id.return_value = mock_chunk_data

        rag = RAGSystem.__new__(RAGSystem)
        rag.is_initialized = True
        rag.vector_store = mock_components["vector_store"]

        # Test
        result = rag.get_chunk("test_001")

        # Assertions
        assert result == mock_chunk_data
        mock_components["vector_store"].get_chunk_by_id.assert_called_once_with(
            "test_001"
        )

    def test_delete_chunk_delegation(self, mock_components):
        """Test that delete_chunk delegates to vector_store."""
        mock_components["vector_store"].delete_chunk.return_value = True

        rag = RAGSystem.__new__(RAGSystem)
        rag.is_initialized = True
        rag.vector_store = mock_components["vector_store"]

        # Test
        result = rag.delete_chunk("test_001")

        # Assertions
        assert result is True
        mock_components["vector_store"].delete_chunk.assert_called_once_with("test_001")

    def test_get_system_stats_success(self, mock_components):
        """Test successful system statistics retrieval."""
        # Setup mock returns
        mock_components["vector_store"].get_stats.return_value = {
            "total_objects": 100,
            "class_name": "Document",
            "is_connected": True,
        }
        mock_components["retriever"].get_retrieval_stats.return_value = {
            "vector_store_stats": {},
            "embedding_model": "all-mpnet-base-v2",
            "embedding_dimension": 768,
        }
        mock_components["embedding_engine"].get_model_info.return_value = {
            "model_name": "all-mpnet-base-v2",
            "dimension": 768,
        }

        rag = RAGSystem.__new__(RAGSystem)
        rag.is_initialized = True
        rag.vector_store = mock_components["vector_store"]
        rag.retriever = mock_components["retriever"]
        rag.embedding_engine = mock_components["embedding_engine"]
        rag.data_chunker = mock_components["data_chunker"]
        rag.data_chunker.chunk_size = 768
        rag.data_chunker.overlap = 100
        rag.logger = Mock()

        # Test
        stats = rag.get_system_stats()

        # Assertions
        assert stats["system_initialized"] is True
        assert stats["vector_store"]["total_objects"] == 100
        assert stats["embedding_engine"]["model_name"] == "all-mpnet-base-v2"
        assert stats["data_chunker"]["chunk_size"] == 768
        assert stats["data_chunker"]["overlap"] == 100
        assert "components" in stats

    def test_get_system_stats_error_handling(self, mock_components):
        """Test error handling in get_system_stats."""
        mock_components["vector_store"].get_stats.side_effect = Exception(
            "Stats failed"
        )

        rag = RAGSystem.__new__(RAGSystem)
        rag.is_initialized = True
        rag.vector_store = mock_components["vector_store"]
        rag.retriever = mock_components["retriever"]
        rag.embedding_engine = mock_components["embedding_engine"]
        rag.data_chunker = mock_components["data_chunker"]
        rag.logger = Mock()

        with pytest.raises(Exception, match="Stats failed"):
            rag.get_system_stats()

    def test_clear_database_success(self, mock_components):
        """Test successful database clearing."""
        rag = RAGSystem.__new__(RAGSystem)
        rag.is_initialized = True
        rag.vector_store = mock_components["vector_store"]
        rag.logger = Mock()

        # Test
        rag.clear_database()

        # Assertions
        mock_components["vector_store"].clear_all.assert_called_once()

    def test_clear_database_not_initialized(self):
        """Test database clearing when system not initialized."""
        rag = RAGSystem.__new__(RAGSystem)
        rag.is_initialized = False

        with pytest.raises(RuntimeError, match="RAG system not initialized"):
            rag.clear_database()

    def test_close_success(self, mock_components):
        """Test successful system closure."""
        rag = RAGSystem.__new__(RAGSystem)
        rag.is_initialized = True
        rag.vector_store = mock_components["vector_store"]
        rag.logger = Mock()

        # Test
        rag.close()

        # Assertions
        assert rag.is_initialized is False
        mock_components["vector_store"].close.assert_called_once()

    def test_close_without_vector_store(self):
        """Test system closure without vector store."""
        rag = RAGSystem.__new__(RAGSystem)
        rag.is_initialized = True
        rag.logger = Mock()

        # Test (should not raise exception)
        rag.close()

        # Assertions
        assert rag.is_initialized is False

    def test_context_manager_success(self, mock_components):
        """Test RAGSystem as context manager."""
        mock_components["vector_store"].close.return_value = None

        rag = RAGSystem.__new__(RAGSystem)
        rag.is_initialized = True
        rag.vector_store = mock_components["vector_store"]
        rag.logger = Mock()

        # Test
        with rag as system:
            assert system.is_initialized is True

        # Assertions
        assert rag.is_initialized is False
        mock_components["vector_store"].close.assert_called_once()

    def test_context_manager_with_exception(self, mock_components):
        """Test RAGSystem context manager with exception."""
        mock_components["vector_store"].close.return_value = None

        rag = RAGSystem.__new__(RAGSystem)
        rag.is_initialized = True
        rag.vector_store = mock_components["vector_store"]
        rag.logger = Mock()

        # Test
        try:
            with rag as system:
                assert system.is_initialized is True
                raise Exception("Test exception")
        except Exception:
            pass

        # Assertions
        assert rag.is_initialized is False
        mock_components["vector_store"].close.assert_called_once()

    def test_query_with_no_similarity_scores(self, mock_components):
        """Test query with results that have no similarity scores."""
        results_without_scores = [
            {"content": "test 1", "chunk_id": "001"},
            {"content": "test 2", "chunk_id": "002"},
        ]
        mock_components["retriever"].search_similar.return_value = (
            results_without_scores
        )

        rag = RAGSystem.__new__(RAGSystem)
        rag.is_initialized = True
        rag.retriever = mock_components["retriever"]
        rag.logger = Mock()

        # Test
        result = rag.query("test question")

        # Assertions
        assert "avg_similarity" not in result
        assert "max_similarity" not in result
        assert result["num_chunks"] == 2

    def test_query_with_mixed_similarity_scores(self, mock_components):
        """Test query with mixed similarity scores."""
        mixed_results = [
            {"content": "test 1", "chunk_id": "001", "similarity_score": 0.8},
            {"content": "test 2", "chunk_id": "002"},  # No similarity score
        ]
        mock_components["retriever"].search_similar.return_value = mixed_results

        rag = RAGSystem.__new__(RAGSystem)
        rag.is_initialized = True
        rag.retriever = mock_components["retriever"]
        rag.logger = Mock()

        # Test
        result = rag.query("test question")

        # Assertions
        assert result["avg_similarity"] == 0.4  # (0.8 + 0) / 2
        assert result["max_similarity"] == 0.8
        assert result["num_chunks"] == 2
