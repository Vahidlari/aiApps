"""Unit tests for refactored Retriever class."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from weaviate.classes.query import Filter, MetadataQuery
from weaviate.exceptions import WeaviateBaseError

from ragora.core.database_manager import DatabaseManager
from ragora.core.embedding_engine import EmbeddingEngine
from ragora.core.retriever import Retriever


class TestRetriever:
    """Test cases for refactored Retriever class."""

    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock DatabaseManager."""
        db_manager = Mock(spec=DatabaseManager)
        db_manager.is_connected = True
        db_manager.url = "http://localhost:8080"
        db_manager.list_collections.return_value = ["Document"]
        return db_manager

    @pytest.fixture
    def mock_collection(self):
        """Create a mock Weaviate collection."""
        collection = Mock()
        return collection

    @pytest.fixture
    def mock_embedding_engine(self):
        """Create a mock EmbeddingEngine."""
        engine = Mock(spec=EmbeddingEngine)
        engine.model_name = "test-model"
        engine.embedding_dimension = 768
        return engine

    @pytest.fixture
    def retriever(self, mock_db_manager, mock_embedding_engine):
        """Create a Retriever instance with mocked dependencies."""
        return Retriever(
            db_manager=mock_db_manager,
            embedding_engine=mock_embedding_engine,
        )

    @pytest.fixture
    def mock_search_result(self):
        """Create a mock search result object."""
        obj = Mock()
        obj.properties = {
            "content": "This is test content about machine learning",
            "chunk_id": "test_chunk_1",
            "source_document": "test_doc.pdf",
            "chunk_type": "text",
            "metadata_chunk_id": 1,
            "metadata_chunk_size": 100,
            "metadata_total_chunks": 5,
            "metadata_created_at": "2023-01-01T00:00:00",
            "page_number": 1,
            "section_title": "Machine Learning",
        }

        # Mock metadata for different search types
        obj.metadata = Mock()
        obj.metadata.distance = 0.2  # For vector search
        obj.metadata.score = 0.8  # For hybrid/keyword search

        return obj

    def test_init_success(self, mock_db_manager, mock_embedding_engine):
        """Test successful initialization of Retriever."""
        retriever = Retriever(
            db_manager=mock_db_manager,
            embedding_engine=mock_embedding_engine,
        )

        assert retriever.db_manager == mock_db_manager
        assert retriever.embedding_engine == mock_embedding_engine

    def test_init_with_default_embedding_engine(self, mock_db_manager):
        """Test initialization with default EmbeddingEngine."""
        with patch("ragora.core.retriever.EmbeddingEngine") as mock_engine_class:
            mock_engine = Mock(spec=EmbeddingEngine)
            mock_engine_class.return_value = mock_engine

            retriever = Retriever(
                db_manager=mock_db_manager,
            )

            assert retriever.embedding_engine == mock_engine
            mock_engine_class.assert_called_once()

    def test_init_with_none_db_manager(self):
        """Test initialization with None DatabaseManager."""
        with pytest.raises(ValueError, match="DatabaseManager cannot be None"):
            Retriever(db_manager=None)

    def test_preprocess_query(self, retriever):
        """Test query preprocessing."""
        query = "  This   is   a   test   query  "
        result = retriever._preprocess_query(query)

        assert result == "this is a test query"

    def test_search_similar_success(
        self, retriever, mock_db_manager, mock_collection, mock_search_result
    ):
        """Test successful vector similarity search."""
        mock_result = Mock()
        mock_result.objects = [mock_search_result]
        mock_collection.query.near_text.return_value = mock_result
        mock_db_manager.get_collection.return_value = mock_collection

        with patch.object(
            retriever, "_preprocess_query", return_value="machine learning"
        ):
            with patch.object(retriever, "_process_vector_results") as mock_process:
                mock_process.return_value = [
                    {"content": "test", "similarity_score": 0.8}
                ]

                result = retriever.search_similar(
                    "machine learning", class_name="Document", top_k=5
                )

                assert len(result) == 1
                mock_collection.query.near_text.assert_called_once_with(
                    query="machine learning",
                    limit=5,
                    return_metadata=MetadataQuery(distance=True),
                )

    def test_search_similar_empty_query(self, retriever):
        """Test vector similarity search with empty query."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            retriever.search_similar("", class_name="Document")

    def test_search_similar_failure(self, retriever, mock_db_manager, mock_collection):
        """Test vector similarity search failure."""
        mock_collection.query.near_text.side_effect = Exception("Search failed")
        mock_db_manager.get_collection.return_value = mock_collection

        with patch.object(
            retriever, "_preprocess_query", return_value="machine learning"
        ):
            with pytest.raises(Exception, match="Search failed"):
                retriever.search_similar("machine learning", class_name="Document")

    def test_search_hybrid_success(
        self, retriever, mock_db_manager, mock_collection, mock_search_result
    ):
        """Test successful hybrid search."""
        mock_result = Mock()
        mock_result.objects = [mock_search_result]
        mock_collection.query.hybrid.return_value = mock_result
        mock_db_manager.get_collection.return_value = mock_collection

        with patch.object(
            retriever, "_preprocess_query", return_value="machine learning"
        ):
            with patch.object(retriever, "_process_hybrid_results") as mock_process:
                mock_process.return_value = [{"content": "test", "hybrid_score": 0.8}]

                result = retriever.search_hybrid(
                    "machine learning", class_name="Document", alpha=0.7, top_k=5
                )

                assert len(result) == 1
                mock_collection.query.hybrid.assert_called_once_with(
                    query="machine learning",
                    alpha=0.7,
                    limit=5,
                    return_metadata=MetadataQuery(score=True),
                )

    def test_search_hybrid_invalid_alpha(self, retriever):
        """Test hybrid search with invalid alpha value."""
        with pytest.raises(ValueError, match="Alpha must be between 0.0 and 1.0"):
            retriever.search_hybrid(
                "machine learning", class_name="Document", alpha=1.5
            )

    def test_search_hybrid_empty_query(self, retriever):
        """Test hybrid search with empty query."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            retriever.search_hybrid("", class_name="Document")

    def test_search_keyword_success(
        self, retriever, mock_db_manager, mock_collection, mock_search_result
    ):
        """Test successful keyword search."""
        mock_result = Mock()
        mock_result.objects = [mock_search_result]
        mock_collection.query.bm25.return_value = mock_result
        mock_db_manager.get_collection.return_value = mock_collection

        with patch.object(
            retriever, "_preprocess_query", return_value="machine learning"
        ):
            with patch.object(retriever, "_process_keyword_results") as mock_process:
                mock_process.return_value = [{"content": "test", "bm25_score": 0.8}]

                result = retriever.search_keyword(
                    "machine learning", class_name="Document", top_k=5
                )

                assert len(result) == 1
                mock_collection.query.bm25.assert_called_once_with(
                    query="machine learning",
                    limit=5,
                    return_metadata=MetadataQuery(score=True),
                )

    def test_search_keyword_empty_query(self, retriever):
        """Test keyword search with empty query."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            retriever.search_keyword("", class_name="Document")

    def test_process_vector_results(self, retriever, mock_search_result):
        """Test processing vector search results."""
        objects = [mock_search_result]

        result = retriever._process_vector_results(objects, score_threshold=0.5)

        assert len(result) == 1
        assert result[0]["similarity_score"] == 0.8  # 1.0 - 0.2
        assert result[0]["distance"] == 0.2
        assert result[0]["retrieval_method"] == "vector_similarity"
        assert "retrieval_timestamp" in result[0]

    def test_process_vector_results_score_threshold(
        self, retriever, mock_search_result
    ):
        """Test processing vector search results with score threshold."""
        objects = [mock_search_result]

        result = retriever._process_vector_results(objects, score_threshold=0.9)

        # Score is 0.8, threshold is 0.9, so no results should be returned
        assert len(result) == 0

    def test_process_hybrid_results(self, retriever, mock_search_result):
        """Test processing hybrid search results."""
        objects = [mock_search_result]

        result = retriever._process_hybrid_results(objects, score_threshold=0.5)

        assert len(result) == 1
        assert result[0]["hybrid_score"] == 0.8
        assert result[0]["similarity_score"] == 0.8
        assert result[0]["retrieval_method"] == "hybrid_search"
        assert "retrieval_timestamp" in result[0]

    def test_process_keyword_results(self, retriever, mock_search_result):
        """Test processing keyword search results."""
        objects = [mock_search_result]

        result = retriever._process_keyword_results(objects, score_threshold=0.5)

        assert len(result) == 1
        assert result[0]["bm25_score"] == 0.8
        assert result[0]["similarity_score"] == 0.8
        assert result[0]["retrieval_method"] == "keyword_search"
        assert "retrieval_timestamp" in result[0]

    def test_get_current_timestamp(self, retriever):
        """Test getting current timestamp."""
        with patch("datetime.datetime") as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = (
                "2023-01-01T00:00:00"
            )

            result = retriever._get_current_timestamp()

            assert result == "2023-01-01T00:00:00"

    def test_get_retrieval_stats_success(
        self, retriever, mock_db_manager, mock_embedding_engine
    ):
        """Test successful retrieval stats."""
        result = retriever.get_retrieval_stats(class_name="Document")

        expected = {
            "database_stats": {
                "is_connected": True,
                "url": "http://localhost:8080",
                "collections": ["Document"],
            },
            "class_name": "Document",
            "embedding_model": "test-model",
            "embedding_dimension": 768,
            "retrieval_methods": [
                "vector_similarity",
                "hybrid_search",
                "keyword_search",
            ],
        }

        assert result == expected

    def test_get_retrieval_stats_failure(self, retriever, mock_db_manager):
        """Test retrieval stats failure."""
        mock_db_manager.list_collections.side_effect = Exception("Stats failed")

        with pytest.raises(Exception, match="Stats failed"):
            retriever.get_retrieval_stats(class_name="Document")
