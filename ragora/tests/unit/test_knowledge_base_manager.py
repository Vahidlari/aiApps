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
from weaviate.classes.query import Filter

from ragora import (
    DatabaseManager,
    DataChunk,
    DataChunker,
    DocumentPreprocessor,
    EmbeddingEngine,
    FilterBuilder,
    KnowledgeBaseManager,
    RetrievalResultItem,
    Retriever,
    SearchResult,
    SearchStrategy,
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
                    chunk_idx=1,
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
                    chunk_idx=2,
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
        from ragora.core.models import RetrievalMetadata, SearchResultItem

        return [
            SearchResultItem(
                content="Test content 1",
                chunk_id="test_001",
                properties={
                    "content": "Test content 1",
                    "chunk_id": "test_001",
                    "source_document": "test.tex",
                    "chunk_type": "text",
                },
                similarity_score=0.85,
                retrieval_method="vector_similarity",
                metadata=RetrievalMetadata(
                    source_document="test.tex",
                    chunk_type="text",
                ),
            ),
            SearchResultItem(
                content="Test content 2",
                chunk_id="test_002",
                properties={
                    "content": "Test content 2",
                    "chunk_id": "test_002",
                    "source_document": "test.tex",
                    "chunk_type": "equation",
                },
                similarity_score=0.75,
                retrieval_method="vector_similarity",
                metadata=RetrievalMetadata(
                    source_document="test.tex",
                    chunk_type="equation",
                ),
            ),
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
        kbm = KnowledgeBaseManager(weaviate_url="http://localhost:8080")

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
                sample_chunks, collection="Document"
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

    def test_search_similar_success(self, mock_components, sample_search_results):
        """Test successful search with similar strategy."""
        mock_components["retriever"].search_similar.return_value = sample_search_results

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.retriever = mock_components["retriever"]
        kbm.logger = Mock()

        # Test
        result = kbm.search(
            "What is the test content?", strategy=SearchStrategy.SIMILAR, top_k=5
        )

        # Assertions
        assert isinstance(result, SearchResult)
        assert result.query == "What is the test content?"
        assert result.strategy == "similar"
        assert result.collection == "Document"
        assert result.total_found == 2
        assert len(result.results) == len(sample_search_results)
        # Compare individual properties
        assert result.results[0].content == sample_search_results[0].content
        assert result.results[0].chunk_id == sample_search_results[0].chunk_id
        assert result.results[1].content == sample_search_results[1].content
        assert result.results[1].chunk_id == sample_search_results[1].chunk_id
        assert "test.tex" in result.metadata["chunk_sources"]
        assert "text" in result.metadata["chunk_types"]
        assert "equation" in result.metadata["chunk_types"]
        assert result.metadata["avg_similarity"] == 0.8  # (0.85 + 0.75) / 2
        assert result.metadata["max_similarity"] == 0.85
        assert result.execution_time > 0
        # Verify SearchResultItem instances (check properties instead of isinstance
        # since Pydantic 2.x may reconstruct instances differently)
        from pydantic import BaseModel

        assert isinstance(result.results[0], BaseModel)
        assert isinstance(result.results[1], BaseModel)
        # Verify they have SearchResultItem attributes
        assert hasattr(result.results[0], "content")
        assert hasattr(result.results[0], "chunk_id")
        assert hasattr(result.results[0], "similarity_score")

        mock_components["retriever"].search_similar.assert_called_once_with(
            "What is the test content?", collection="Document", top_k=5, filter=None
        )

    def test_search_hybrid_success(self, mock_components, sample_search_results):
        """Test successful search with hybrid strategy."""
        mock_components["retriever"].search_hybrid.return_value = sample_search_results

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.retriever = mock_components["retriever"]
        kbm.logger = Mock()

        # Test
        result = kbm.search(
            "What is the test content?", strategy=SearchStrategy.HYBRID, top_k=3
        )

        # Assertions
        assert isinstance(result, SearchResult)
        assert result.strategy == "hybrid"
        mock_components["retriever"].search_hybrid.assert_called_once_with(
            "What is the test content?", collection="Document", top_k=3, filter=None
        )

    def test_search_keyword_success(self, mock_components, sample_search_results):
        """Test successful search with keyword strategy."""
        mock_components["retriever"].search_keyword.return_value = sample_search_results

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.retriever = mock_components["retriever"]
        kbm.logger = Mock()

        # Test
        result = kbm.search(
            "machine learning algorithms", strategy=SearchStrategy.KEYWORD, top_k=3
        )

        # Assertions
        assert isinstance(result, SearchResult)
        assert result.strategy == "keyword"
        mock_components["retriever"].search_keyword.assert_called_once_with(
            "machine learning algorithms", collection="Document", top_k=3, filter=None
        )

    def test_search_invalid_strategy(self, mock_components):
        """Test search with invalid strategy."""
        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.retriever = mock_components["retriever"]
        kbm.logger = Mock()

        with pytest.raises(ValueError, match="Invalid search strategy"):
            kbm.search("test", strategy="invalid")

    def test_search_empty_query(self, mock_components):
        """Test search with empty query."""
        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.retriever = mock_components["retriever"]
        kbm.logger = Mock()

        with pytest.raises(ValueError, match="Query cannot be empty"):
            kbm.search("")

    def test_search_not_initialized(self):
        """Test search when system not initialized."""
        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = False

        with pytest.raises(
            RuntimeError, match="Knowledge base manager not initialized"
        ):
            kbm.search("test question")

    def test_search_with_filter_similar(self, mock_components, sample_search_results):
        """Test search with filter using similar strategy."""
        mock_components["retriever"].search_similar.return_value = sample_search_results

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.retriever = mock_components["retriever"]
        kbm.logger = Mock()

        # Create filter using FilterBuilder
        test_filter = FilterBuilder.by_chunk_type("text")

        # Test
        result = kbm.search(
            "What is the test content?",
            strategy=SearchStrategy.SIMILAR,
            top_k=5,
            filter=test_filter,
        )

        # Assertions
        assert isinstance(result, SearchResult)
        assert result.strategy == "similar"
        mock_components["retriever"].search_similar.assert_called_once_with(
            "What is the test content?",
            collection="Document",
            top_k=5,
            filter=test_filter,
        )

    def test_search_with_filter_hybrid(self, mock_components, sample_search_results):
        """Test search with filter using hybrid strategy."""
        mock_components["retriever"].search_hybrid.return_value = sample_search_results

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.retriever = mock_components["retriever"]
        kbm.logger = Mock()

        # Create filter using FilterBuilder
        test_filter = FilterBuilder.by_source_document("test.pdf")

        # Test
        result = kbm.search(
            "What is the test content?",
            strategy=SearchStrategy.HYBRID,
            top_k=3,
            filter=test_filter,
        )

        # Assertions
        assert isinstance(result, SearchResult)
        assert result.strategy == "hybrid"
        mock_components["retriever"].search_hybrid.assert_called_once_with(
            "What is the test content?",
            collection="Document",
            top_k=3,
            filter=test_filter,
        )

    def test_search_with_filter_keyword(self, mock_components, sample_search_results):
        """Test search with filter using keyword strategy."""
        mock_components["retriever"].search_keyword.return_value = sample_search_results

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.retriever = mock_components["retriever"]
        kbm.logger = Mock()

        # Create filter using raw Filter object
        test_filter = Filter.by_property("chunk_type").equal("text")

        # Test
        result = kbm.search(
            "machine learning algorithms",
            strategy=SearchStrategy.KEYWORD,
            top_k=3,
            filter=test_filter,
        )

        # Assertions
        assert isinstance(result, SearchResult)
        assert result.strategy == "keyword"
        mock_components["retriever"].search_keyword.assert_called_once_with(
            "machine learning algorithms",
            collection="Document",
            top_k=3,
            filter=test_filter,
        )

    def test_search_with_combined_filter(self, mock_components, sample_search_results):
        """Test search with combined filters."""
        mock_components["retriever"].search_hybrid.return_value = sample_search_results

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.retriever = mock_components["retriever"]
        kbm.logger = Mock()

        # Create combined filter
        filter1 = FilterBuilder.by_chunk_type("text")
        filter2 = FilterBuilder.by_source_document("test.pdf")
        combined_filter = FilterBuilder.combine_and(filter1, filter2)

        # Test
        result = kbm.search(
            "What is the test content?",
            strategy=SearchStrategy.HYBRID,
            top_k=3,
            filter=combined_filter,
        )

        # Assertions
        assert isinstance(result, SearchResult)
        mock_components["retriever"].search_hybrid.assert_called_once_with(
            "What is the test content?",
            collection="Document",
            top_k=3,
            filter=combined_filter,
        )

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
        stats = kbm.get_collection_stats("Document")

        # Assertions
        assert stats["collection"] == "Document"
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

    def test_get_collection_stats_error_handling(self, mock_components):
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
            kbm.get_collection_stats("Document")

    def test_clear_collection_success(self, mock_components):
        """Test successful database clearing."""
        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.vector_store = mock_components["vector_store"]
        kbm.logger = Mock()

        # Test
        kbm.clear_collection("Document")

        # Assertions
        mock_components["vector_store"].clear_all.assert_called_once_with(
            collection="Document"
        )

    def test_clear_collection_not_initialized(self):
        """Test collection clearing when system not initialized."""
        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = False

        with pytest.raises(
            RuntimeError, match="Knowledge base manager not initialized"
        ):
            kbm.clear_collection("Document")

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
        from ragora.core.models import RetrievalMetadata, SearchResultItem

        results_without_scores = [
            SearchResultItem(
                content="test 1",
                chunk_id="001",
                properties={"content": "test 1", "chunk_id": "001"},
                similarity_score=0.0,
                retrieval_method="vector_similarity",
                metadata=RetrievalMetadata(),
            ),
            SearchResultItem(
                content="test 2",
                chunk_id="002",
                properties={"content": "test 2", "chunk_id": "002"},
                similarity_score=0.0,
                retrieval_method="vector_similarity",
                metadata=RetrievalMetadata(),
            ),
        ]
        mock_components["retriever"].search_similar.return_value = (
            results_without_scores
        )

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.retriever = mock_components["retriever"]
        kbm.logger = Mock()

        # Test
        result = kbm.search("test question", strategy=SearchStrategy.SIMILAR)

        # Assertions
        assert isinstance(result, SearchResult)
        assert result.metadata["avg_similarity"] == 0.0
        assert result.metadata["max_similarity"] == 0.0
        assert result.total_found == 2

    def test_query_with_mixed_similarity_scores(self, mock_components):
        """Test query with mixed similarity scores."""
        from ragora.core.models import RetrievalMetadata, SearchResultItem

        mixed_results = [
            SearchResultItem(
                content="test 1",
                chunk_id="001",
                properties={"content": "test 1", "chunk_id": "001"},
                similarity_score=0.8,
                retrieval_method="vector_similarity",
                metadata=RetrievalMetadata(),
            ),
            SearchResultItem(
                content="test 2",
                chunk_id="002",
                properties={"content": "test 2", "chunk_id": "002"},
                similarity_score=0.0,  # No similarity score
                retrieval_method="vector_similarity",
                metadata=RetrievalMetadata(),
            ),
        ]
        mock_components["retriever"].search_similar.return_value = mixed_results

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.retriever = mock_components["retriever"]
        kbm.logger = Mock()

        # Test
        result = kbm.search("test question", strategy=SearchStrategy.SIMILAR)

        # Assertions
        assert isinstance(result, SearchResult)
        assert result.metadata["avg_similarity"] == 0.4  # (0.8 + 0) / 2
        assert result.metadata["max_similarity"] == 0.8
        assert result.total_found == 2

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

    def test_list_collections(self, mock_components):
        """Test list_collections method."""
        mock_components["db_manager"].list_collections.return_value = [
            "Document",
            "Email",
        ]

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.db_manager = mock_components["db_manager"]

        # Test
        collections = kbm.list_collections()

        # Assertions
        assert collections == ["Document", "Email"]
        mock_components["db_manager"].list_collections.assert_called_once()

    def test_create_collection_success(self, mock_components):
        """Test successful collection creation."""
        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.vector_store = mock_components["vector_store"]
        kbm.logger = Mock()

        # Test
        result = kbm.create_collection("TestCollection")

        # Assertions
        assert result is True
        mock_components["vector_store"].create_schema.assert_called_once_with(
            "TestCollection", force_recreate=False
        )

    def test_create_collection_failure(self, mock_components):
        """Test collection creation failure."""
        mock_components["vector_store"].create_schema.side_effect = Exception(
            "Creation failed"
        )

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.vector_store = mock_components["vector_store"]
        kbm.logger = Mock()

        # Test
        result = kbm.create_collection("TestCollection")

        # Assertions
        assert result is False

    def test_delete_collection_success(self, mock_components):
        """Test successful collection deletion."""
        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.vector_store = mock_components["vector_store"]
        kbm.logger = Mock()

        # Test
        result = kbm.delete_collection("TestCollection")

        # Assertions
        assert result is True
        mock_components["vector_store"].clear_all.assert_called_once_with(
            collection="TestCollection"
        )

    def test_delete_collection_failure(self, mock_components):
        """Test collection deletion failure."""
        mock_components["vector_store"].clear_all.side_effect = Exception(
            "Deletion failed"
        )

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.vector_store = mock_components["vector_store"]
        kbm.logger = Mock()

        # Test
        result = kbm.delete_collection("TestCollection")

        # Assertions
        assert result is False

    def test_get_chunk_success(self, mock_components):
        """Test successful chunk retrieval."""
        # Create using model_validate to avoid Pydantic validation issues
        mock_result = RetrievalResultItem.model_validate(
            {
                "content": "test content",
                "chunk_id": "test_chunk_1",
                "properties": {"content": "test content", "chunk_id": "test_chunk_1"},
            }
        )
        mock_components["vector_store"].get_chunk_by_id.return_value = mock_result

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.vector_store = mock_components["vector_store"]
        kbm.logger = Mock()

        # Test
        result = kbm.get_chunk("test_chunk_1", "TestCollection")

        # Assertions
        assert result is not None
        assert isinstance(result, RetrievalResultItem)
        assert result.content == "test content"
        assert result.chunk_id == "test_chunk_1"
        mock_components["vector_store"].get_chunk_by_id.assert_called_once_with(
            "test_chunk_1", collection="TestCollection"
        )

    def test_get_chunk_not_found(self, mock_components):
        """Test chunk retrieval when chunk not found."""
        mock_components["vector_store"].get_chunk_by_id.return_value = None

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.vector_store = mock_components["vector_store"]
        kbm.logger = Mock()

        # Test
        result = kbm.get_chunk("nonexistent_chunk", "TestCollection")

        # Assertions
        assert result is None

    def test_get_chunk_with_metadata(self, mock_components):
        """Test chunk retrieval with metadata extraction."""
        # Create using model_validate with metadata dict
        mock_result = RetrievalResultItem.model_validate(
            {
                "content": "test content",
                "chunk_id": "test_chunk_1",
                "properties": {
                    "content": "test content",
                    "chunk_id": "test_chunk_1",
                    "source_document": "test_doc.pdf",
                    "page_number": 1,
                },
                "metadata": {
                    "source_document": "test_doc.pdf",
                    "page_number": 1,
                },
            }
        )
        mock_components["vector_store"].get_chunk_by_id.return_value = mock_result

        kbm = KnowledgeBaseManager.__new__(KnowledgeBaseManager)
        kbm.is_initialized = True
        kbm.vector_store = mock_components["vector_store"]
        kbm.logger = Mock()

        # Test
        result = kbm.get_chunk("test_chunk_1", "TestCollection")

        # Assertions
        assert result is not None
        assert result.metadata.source_document == "test_doc.pdf"
        assert result.metadata.page_number == 1
