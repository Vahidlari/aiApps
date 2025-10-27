"""Unit tests for the KnowledgeBaseManager module.

This module contains comprehensive unit tests for the KnowledgeBaseManager class,
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

from ragora import (
    DatabaseManager,
    DataChunk,
    DataChunker,
    DocumentPreprocessor,
    EmbeddingEngine,
    KnowledgeBaseManager,
    Retriever,
    VectorStore,
)


class TestKnowledgeBaseManager:
    """Test suite for KnowledgeBaseManager class."""

    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing."""
        mock_db_manager = Mock(spec=DatabaseManager)
        mock_vector_store = Mock(spec=VectorStore)
        mock_retriever = Mock(spec=Retriever)
        mock_embedding_engine = Mock(spec=EmbeddingEngine)
        mock_document_preprocessor = Mock(spec=DocumentPreprocessor)
        mock_data_chunker = Mock(spec=DataChunker)

        return {
            "db_manager": mock_db_manager,
            "vector_store": mock_vector_store,
            "retriever": mock_retriever,
            "embedding_engine": mock_embedding_engine,
            "document_preprocessor": mock_document_preprocessor,
            "data_chunker": mock_data_chunker,
        }

    @pytest.fixture
    def sample_chunks(self):
        """Create sample DataChunk objects for testing."""
        from ragora.core.chunking import ChunkMetadata

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

    @patch("ragora.ragora.core.knowledge_base_manager.DatabaseManager")
    @patch("ragora.ragora.core.knowledge_base_manager.VectorStore")
    @patch("ragora.ragora.core.knowledge_base_manager.Retriever")
    @patch("ragora.ragora.core.knowledge_base_manager.DocumentPreprocessor")
    def test_knowledge_base_manager_initialization_success(
        self,
        mock_document_preprocessor,
        mock_retriever,
        mock_vector_store,
        mock_db_manager,
    ):
        """Test successful KnowledgeBaseManager initialization."""
        # Setup mocks
        mock_db_manager.return_value = Mock()
        mock_vector_store.return_value = Mock()
        mock_retriever.return_value = Mock()
        mock_document_preprocessor.return_value = Mock()

        # Test
        kbm = KnowledgeBaseManager(
            weaviate_url="http://localhost:8080", class_name="TestDocument"
        )

        # Assertions
        assert kbm.is_initialized is True
        assert kbm.embedding_engine is None  # Not initialized by default
        assert kbm.data_chunker is None  # Not initialized by KnowledgeBaseManager
        mock_db_manager.assert_called_once_with(url="http://localhost:8080")
        mock_vector_store.assert_called_once()
        mock_retriever.assert_called_once()
        mock_document_preprocessor.assert_called_once_with(chunker=None)

    def test_process_document_success(self, mock_components, sample_chunks):
        """Test successful document processing."""
        # Setup
        mock_components["document_preprocessor"].preprocess_document.return_value = (
            sample_chunks
        )
        mock_components["vector_store"].store_chunks.return_value = ["uuid1", "uuid2"]

        # Create knowledge base manager with mocked components
        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.document_preprocessor = mock_components["document_preprocessor"]
        kbm.vector_store = mock_components["vector_store"]
        kbm.logger = Mock()

        # Test
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", delete=False) as f:
            f.write(
                "\\documentclass{article}\\begin{document}Test content\\end{document}"
            )
            temp_path = f.name

        try:
            result = kbm.process_document(temp_path)

            # Assertions
            assert result == ["uuid1", "uuid2"]
            mock_components[
                "document_preprocessor"
            ].preprocess_document.assert_called_once_with(temp_path, "latex")
            mock_components["vector_store"].store_chunks.assert_called_once_with(
                sample_chunks, class_name="Document"
            )
        finally:
            os.unlink(temp_path)

    def test_process_document_not_initialized(self):
        """Test document processing when system not initialized."""
        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = False

        with pytest.raises(
            RuntimeError, match="Knowledge base manager not initialized"
        ):
            kbm.process_document("test.tex")

    def test_process_document_file_not_found(self, mock_components):
        """Test document processing with non-existent file."""
        mock_components["document_preprocessor"].preprocess_document.side_effect = (
            FileNotFoundError("File not found")
        )

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.document_preprocessor = mock_components["document_preprocessor"]
        kbm.data_chunker = mock_components["data_chunker"]
        kbm.vector_store = mock_components["vector_store"]
        kbm.logger = Mock()

        with pytest.raises(FileNotFoundError, match="File not found"):
            kbm.process_document("nonexistent.tex")

    def test_query_similar_success(self, mock_components, sample_search_results):
        """Test successful query with similar search."""
        mock_components["retriever"].search_similar.return_value = sample_search_results

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.retriever = mock_components["retriever"]
        kbm.logger = Mock()

        # Test
        result = kbm.query("What is the test content?", search_type="similar", top_k=5)

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
            "What is the test content?", top_k=5, class_name="Document"
        )

    def test_query_hybrid_success(self, mock_components, sample_search_results):
        """Test successful query with hybrid search."""
        mock_components["retriever"].search_hybrid.return_value = sample_search_results

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.retriever = mock_components["retriever"]
        kbm.logger = Mock()

        # Test
        result = kbm.query("What is the test content?", search_type="hybrid", top_k=3)

        # Assertions
        assert result["search_type"] == "hybrid"
        mock_components["retriever"].search_hybrid.assert_called_once_with(
            "What is the test content?", top_k=3, class_name="Document"
        )

    def test_query_keyword_success(self, mock_components, sample_search_results):
        """Test successful query with keyword search."""
        mock_components["retriever"].search_keyword.return_value = sample_search_results

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.retriever = mock_components["retriever"]
        kbm.logger = Mock()

        # Test
        result = kbm.query(
            "machine learning algorithms", search_type="keyword", top_k=3
        )

        # Assertions
        assert result["search_type"] == "keyword"
        mock_components["retriever"].search_keyword.assert_called_once_with(
            "machine learning algorithms", top_k=3, class_name="Document"
        )

    def test_query_invalid_search_type(self, mock_components):
        """Test query with invalid search type."""
        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.retriever = mock_components["retriever"]
        kbm.logger = Mock()

        with pytest.raises(ValueError, match="Invalid search type: invalid"):
            kbm.query("test", search_type="invalid")

    def test_query_empty_question(self, mock_components):
        """Test query with empty question."""
        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.retriever = mock_components["retriever"]
        kbm.logger = Mock()

        with pytest.raises(ValueError, match="Question cannot be empty"):
            kbm.query("")

    def test_query_not_initialized(self):
        """Test query when system not initialized."""
        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = False

        with pytest.raises(
            RuntimeError, match="Knowledge base manager not initialized"
        ):
            kbm.query("test question")

    def test_search_similar_delegation(self, mock_components, sample_search_results):
        """Test that search_similar delegates to retriever."""
        mock_components["retriever"].search_similar.return_value = sample_search_results

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.retriever = mock_components["retriever"]

        # Test
        result = kbm.search_similar("test query", top_k=5)

        # Assertions
        assert result == sample_search_results
        mock_components["retriever"].search_similar.assert_called_once_with(
            "test query", top_k=5, class_name="Document"
        )

    def test_search_hybrid_delegation(self, mock_components, sample_search_results):
        """Test that search_hybrid delegates to retriever."""
        mock_components["retriever"].search_hybrid.return_value = sample_search_results

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.retriever = mock_components["retriever"]

        # Test
        result = kbm.search_hybrid("test query", alpha=0.7, top_k=3)

        # Assertions
        assert result == sample_search_results
        mock_components["retriever"].search_hybrid.assert_called_once_with(
            "test query", alpha=0.7, top_k=3, class_name="Document"
        )

    def test_search_keyword_delegation(self, mock_components, sample_search_results):
        """Test that search_keyword delegates to retriever."""
        mock_components["retriever"].search_keyword.return_value = sample_search_results

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.retriever = mock_components["retriever"]

        # Test
        result = kbm.search_keyword("machine learning", top_k=3)

        # Assertions
        assert result == sample_search_results
        mock_components["retriever"].search_keyword.assert_called_once_with(
            "machine learning", top_k=3, class_name="Document"
        )

    def test_get_chunk_delegation(self, mock_components):
        """Test that get_chunk delegates to vector_store."""
        mock_chunk_data = {"chunk_id": "test_001", "content": "test content"}
        mock_components["vector_store"].get_chunk_by_id.return_value = mock_chunk_data

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.vector_store = mock_components["vector_store"]

        # Test
        result = kbm.get_chunk("test_001")

        # Assertions
        assert result == mock_chunk_data
        mock_components["vector_store"].get_chunk_by_id.assert_called_once_with(
            "test_001"
        )

    def test_delete_chunk_delegation(self, mock_components):
        """Test that delete_chunk delegates to vector_store."""
        mock_components["vector_store"].delete_chunk.return_value = True

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.vector_store = mock_components["vector_store"]

        # Test
        result = kbm.delete_chunk("test_001")

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

        # Setup DatabaseManager mock
        mock_components["db_manager"].url = "http://localhost:8080"
        mock_components["db_manager"].is_connected = True
        mock_components["db_manager"].list_collections.return_value = ["Document"]

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.db_manager = mock_components["db_manager"]
        kbm.vector_store = mock_components["vector_store"]
        kbm.retriever = mock_components["retriever"]
        kbm.embedding_engine = mock_components["embedding_engine"]
        kbm.data_chunker = mock_components["data_chunker"]
        # Create a mock strategy for the data_chunker
        mock_strategy = Mock()
        mock_strategy.chunk_size = 768
        mock_strategy.overlap_size = 100
        kbm.data_chunker.default_strategy = mock_strategy
        kbm.logger = Mock()

        # Test
        stats = kbm.get_system_stats()

        # Assertions
        assert stats["system_initialized"] is True
        assert stats["database_manager"]["url"] == "http://localhost:8080"
        assert stats["database_manager"]["is_connected"] is True
        assert stats["database_manager"]["collections"] == ["Document"]
        assert stats["vector_store"]["total_objects"] == 100
        assert stats["embedding_engine"]["model_name"] == "all-mpnet-base-v2"
        assert stats["data_chunker"]["chunk_size"] == 768
        assert stats["data_chunker"]["overlap_size"] == 100
        assert "components" in stats
        assert "architecture" in stats
        assert (
            stats["architecture"]
            == "Three-Layer (DatabaseManager -> VectorStore -> Retriever)"
        )

    def test_get_system_stats_error_handling(self, mock_components):
        """Test error handling in get_system_stats."""
        mock_components["vector_store"].get_stats.side_effect = Exception(
            "Stats failed"
        )

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.db_manager = mock_components["db_manager"]
        kbm.vector_store = mock_components["vector_store"]
        kbm.retriever = mock_components["retriever"]
        kbm.embedding_engine = mock_components["embedding_engine"]
        kbm.data_chunker = mock_components["data_chunker"]
        kbm.logger = Mock()

        with pytest.raises(Exception, match="Stats failed"):
            kbm.get_system_stats()

    def test_clear_database_success(self, mock_components):
        """Test successful database clearing."""
        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.vector_store = mock_components["vector_store"]
        kbm.logger = Mock()

        # Test
        kbm.clear_database()

        # Assertions
        mock_components["vector_store"].clear_all.assert_called_once()

    def test_clear_database_not_initialized(self):
        """Test database clearing when system not initialized."""
        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = False

        with pytest.raises(
            RuntimeError, match="Knowledge base manager not initialized"
        ):
            kbm.clear_database()

    def test_close_success(self, mock_components):
        """Test successful system closure."""
        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.vector_store = mock_components["vector_store"]
        kbm.logger = Mock()

        # Test
        kbm.close()

        # Assertions
        assert kbm.is_initialized is False
        mock_components["vector_store"].close.assert_called_once()

    def test_close_without_vector_store(self):
        """Test system closure without vector store."""
        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.logger = Mock()

        # Test (should not raise exception)
        kbm.close()

        # Assertions
        assert kbm.is_initialized is False

    def test_context_manager_success(self, mock_components):
        """Test KnowledgeBaseManager as context manager."""
        mock_components["vector_store"].close.return_value = None

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.vector_store = mock_components["vector_store"]
        kbm.logger = Mock()

        # Test
        with kbm as system:
            assert system.is_initialized is True

        # Assertions
        assert kbm.is_initialized is False
        mock_components["vector_store"].close.assert_called_once()

    def test_context_manager_with_exception(self, mock_components):
        """Test KnowledgeBaseManager context manager with exception."""
        mock_components["vector_store"].close.return_value = None

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.vector_store = mock_components["vector_store"]
        kbm.logger = Mock()

        # Test
        try:
            with kbm as system:
                assert system.is_initialized is True
                raise Exception("Test exception")
        except Exception:
            pass

        # Assertions
        assert kbm.is_initialized is False
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

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.retriever = mock_components["retriever"]
        kbm.logger = Mock()

        # Test
        result = kbm.query("test question")

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

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.retriever = mock_components["retriever"]
        kbm.logger = Mock()

        # Test
        result = kbm.query("test question")

        # Assertions
        assert result["avg_similarity"] == 0.4  # (0.8 + 0) / 2
        assert result["max_similarity"] == 0.8
        assert result["num_chunks"] == 2

    # Email processing tests

    def test_check_new_emails_success(self, mock_components):
        """Test checking new emails."""
        from ragora.utils.email_utils.models import EmailAddress, EmailMessage

        # Create mock emails
        mock_emails = [
            EmailMessage(
                message_id="msg1",
                subject="Test 1",
                sender=EmailAddress("sender@example.com"),
                recipients=[EmailAddress("recipient@example.com")],
                body_text="Body 1",
            ),
            EmailMessage(
                message_id="msg2",
                subject="Test 2",
                sender=EmailAddress("sender@example.com"),
                recipients=[EmailAddress("recipient@example.com")],
                body_text="Body 2",
            ),
        ]

        # Mock email provider
        mock_provider = Mock()
        mock_provider.is_connected = False
        mock_provider.fetch_messages.return_value = mock_emails

        # Create KBM with email preprocessor
        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.logger = Mock()
        kbm.email_preprocessor = Mock()

        # Test
        result = kbm.check_new_emails(mock_provider)

        # Assertions
        assert result["count"] == 2
        assert len(result["emails"]) == 2
        assert result["emails"][0]["email_id"] == "msg1"
        mock_provider.connect.assert_called_once()
        mock_provider.fetch_messages.assert_called_once()

    def test_process_new_emails_success(self, mock_components):
        """Test processing new emails with specific IDs."""
        from ragora.core.email_preprocessor import EmailPreprocessor
        from ragora.utils.email_utils.models import EmailAddress, EmailMessage

        # Create mock emails
        mock_emails = [
            EmailMessage(
                message_id="msg1",
                subject="Test 1",
                sender=EmailAddress("sender@example.com"),
                recipients=[EmailAddress("recipient@example.com")],
                body_text="Body 1",
            ),
        ]

        # Mock components
        mock_provider = Mock()
        mock_provider.is_connected = True
        mock_provider.fetch_message_by_id.return_value = mock_emails[0]

        mock_email_preprocessor = Mock(spec=EmailPreprocessor)
        mock_email_preprocessor.preprocess_emails.return_value = []

        mock_components["vector_store"].store_chunks.return_value = ["uuid1"]

        # Setup KBM
        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.email_preprocessor = mock_email_preprocessor
        kbm.vector_store = mock_components["vector_store"]
        kbm.logger = Mock()

        # Test with specific email IDs
        email_ids = ["msg1"]
        result = kbm.process_new_emails(mock_provider, email_ids)

        # Assertions
        assert result == ["uuid1"]
        mock_provider.connect.assert_not_called()  # Already connected
        mock_provider.fetch_message_by_id.assert_called_once_with("msg1")
        mock_email_preprocessor.preprocess_emails.assert_called_once()
        mock_components["vector_store"].store_chunks.assert_called_once()

    def test_search_emails_success(self, mock_components):
        """Test searching emails."""
        mock_search_results = [{"content": "email content", "subject": "Test"}]
        mock_components["retriever"].search_similar.return_value = mock_search_results

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.retriever = mock_components["retriever"]
        kbm.logger = Mock()

        # Test
        result = kbm.search_emails("test query", class_name="Email")

        # Assertions
        assert result == mock_search_results
        mock_components["retriever"].search_similar.assert_called_once_with(
            "test query", top_k=5, class_name="Email"
        )

    def test_search_emails_invalid_type(self, mock_components):
        """Test search_emails with invalid search type."""
        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.retriever = mock_components["retriever"]
        kbm.logger = Mock()

        # Test
        with pytest.raises(ValueError, match="Invalid search type"):
            kbm.search_emails("query", search_type="invalid")
