"""Unit tests for refactored Retriever class."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from weaviate.classes.query import Filter, MetadataQuery
from weaviate.exceptions import WeaviateBaseError

from ragora.core.database_manager import DatabaseManager
from ragora.core.embedding_engine import EmbeddingEngine
from ragora.core.models import RetrievalMetadata, RetrievalResultItem, SearchResultItem
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
            "metadata_chunk_idx": 1,
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

    def test_init_without_embedding_engine(self, mock_db_manager):
        """Test initialization without EmbeddingEngine (default None)."""
        retriever = Retriever(
            db_manager=mock_db_manager,
        )

        # EmbeddingEngine should be None by default (Weaviate handles embeddings)
        assert retriever.embedding_engine is None

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
                    SearchResultItem(
                        content="test",
                        chunk_id="test_1",
                        similarity_score=0.8,
                        retrieval_method="vector_similarity",
                    )
                ]

                result = retriever.search_similar(
                    "machine learning", collection="Document", top_k=5
                )

                assert len(result) == 1
                mock_collection.query.near_text.assert_called_once_with(
                    query="machine learning",
                    limit=5,
                    return_metadata=MetadataQuery(distance=True),
                    filter=None,
                )

    def test_search_similar_empty_query(self, retriever):
        """Test vector similarity search with empty query."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            retriever.search_similar("", collection="Document")

    def test_search_similar_failure(self, retriever, mock_db_manager, mock_collection):
        """Test vector similarity search failure."""
        mock_collection.query.near_text.side_effect = Exception("Search failed")
        mock_db_manager.get_collection.return_value = mock_collection

        with patch.object(
            retriever, "_preprocess_query", return_value="machine learning"
        ):
            with pytest.raises(Exception, match="Search failed"):
                retriever.search_similar("machine learning", collection="Document")

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
                mock_process.return_value = [
                    SearchResultItem(
                        content="test",
                        chunk_id="test_1",
                        similarity_score=0.8,
                        hybrid_score=0.8,
                        retrieval_method="hybrid_search",
                    )
                ]

                result = retriever.search_hybrid(
                    "machine learning", collection="Document", alpha=0.7, top_k=5
                )

                assert len(result) == 1
                mock_collection.query.hybrid.assert_called_once_with(
                    query="machine learning",
                    alpha=0.7,
                    limit=5,
                    return_metadata=MetadataQuery(score=True),
                    filter=None,
                )

    def test_search_hybrid_invalid_alpha(self, retriever):
        """Test hybrid search with invalid alpha value."""
        with pytest.raises(ValueError, match="Alpha must be between 0.0 and 1.0"):
            retriever.search_hybrid(
                "machine learning", collection="Document", alpha=1.5
            )

    def test_search_hybrid_empty_query(self, retriever):
        """Test hybrid search with empty query."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            retriever.search_hybrid("", collection="Document")

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
                mock_process.return_value = [
                    SearchResultItem(
                        content="test",
                        chunk_id="test_1",
                        similarity_score=0.8,
                        bm25_score=0.8,
                        retrieval_method="keyword_search",
                    )
                ]

                result = retriever.search_keyword(
                    "machine learning", collection="Document", top_k=5
                )

                assert len(result) == 1
                mock_collection.query.bm25.assert_called_once_with(
                    query="machine learning",
                    limit=5,
                    return_metadata=MetadataQuery(score=True),
                    filter=None,
                )

    def test_search_keyword_empty_query(self, retriever):
        """Test keyword search with empty query."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            retriever.search_keyword("", collection="Document")

    def test_process_vector_results(self, retriever, mock_search_result):
        """Test processing vector search results."""
        objects = [mock_search_result]

        result = retriever._process_vector_results(objects, score_threshold=0.5)

        assert len(result) == 1
        assert isinstance(result[0], SearchResultItem)
        assert result[0].similarity_score == 0.8  # 1.0 - 0.2
        assert result[0].distance == 0.2
        assert result[0].retrieval_method == "vector_similarity"
        assert result[0].retrieval_timestamp is not None

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
        assert isinstance(result[0], SearchResultItem)
        assert result[0].hybrid_score == 0.8
        assert result[0].similarity_score == 0.8
        assert result[0].retrieval_method == "hybrid_search"
        assert result[0].retrieval_timestamp is not None

    def test_process_keyword_results(self, retriever, mock_search_result):
        """Test processing keyword search results."""
        objects = [mock_search_result]

        result = retriever._process_keyword_results(objects, score_threshold=0.5)

        assert len(result) == 1
        assert isinstance(result[0], SearchResultItem)
        assert result[0].bm25_score == 0.8
        assert result[0].similarity_score == 0.8
        assert result[0].retrieval_method == "keyword_search"
        assert result[0].retrieval_timestamp is not None

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
        """Test successful retrieval stats with embedding engine."""
        result = retriever.get_retrieval_stats(collection="Document")

        expected = {
            "database_stats": {
                "is_connected": True,
                "url": "http://localhost:8080",
                "collections": ["Document"],
            },
            "collection": "Document",
            "embedding_model": "test-model",
            "embedding_dimension": 768,
            "retrieval_methods": [
                "vector_similarity",
                "hybrid_search",
                "keyword_search",
            ],
        }

        assert result == expected

    def test_get_retrieval_stats_without_embedding_engine(self, mock_db_manager):
        """Test retrieval stats without embedding engine."""
        retriever = Retriever(db_manager=mock_db_manager)
        result = retriever.get_retrieval_stats(collection="Document")

        assert result["embedding_model"] == (
            "Weaviate text2vec-transformers (server-side)"
        )
        assert result["embedding_dimension"] == "N/A (server-side)"

    def test_get_retrieval_stats_failure(self, retriever, mock_db_manager):
        """Test retrieval stats failure."""
        mock_db_manager.list_collections.side_effect = Exception("Stats failed")

        with pytest.raises(Exception, match="Stats failed"):
            retriever.get_retrieval_stats(collection="Document")

    def test_search_result_item_convenience_properties(self):
        """Test SearchResultItem convenience properties for email results."""
        # Create SearchResultItem with email properties
        result = SearchResultItem(
            content="Test email content",
            chunk_id="email_001",
            properties={
                "email_subject": "Test Subject",
                "email_sender": "sender@example.com",
                "content": "Test email content",
                "chunk_id": "email_001",
            },
            similarity_score=0.9,
            retrieval_method="vector_similarity",
            metadata=RetrievalMetadata(
                email_subject="Test Subject",
                email_sender="sender@example.com",
            ),
        )

        # Test convenience properties
        assert result.subject == "Test Subject"
        assert result.sender == "sender@example.com"

    def test_search_result_item_serialization(self):
        """Test SearchResultItem serialization methods."""
        result = SearchResultItem(
            content="Test content",
            chunk_id="test_001",
            properties={"content": "Test content", "chunk_id": "test_001"},
            similarity_score=0.8,
            retrieval_method="vector_similarity",
        )

        # Test model_dump
        result_dict = result.model_dump()
        assert result_dict["content"] == "Test content"
        assert result_dict["chunk_id"] == "test_001"
        assert result_dict["similarity_score"] == 0.8

        # Test model_dump_json
        result_json = result.model_dump_json()
        assert "Test content" in result_json
        assert "test_001" in result_json

    def test_retrieval_result_item_base_class(self):
        """Test RetrievalResultItem base class functionality."""
        base_result = RetrievalResultItem(
            content="Test content",
            chunk_id="test_001",
            properties={"content": "Test content", "chunk_id": "test_001"},
            metadata=RetrievalMetadata(source_document="test.pdf"),
        )

        # Verify base class fields
        assert base_result.content == "Test content"
        assert base_result.chunk_id == "test_001"
        assert base_result.properties["chunk_id"] == "test_001"
        assert base_result.metadata.source_document == "test.pdf"

        # Verify SearchResultItem fields are not available
        assert not hasattr(base_result, "similarity_score")
        assert not hasattr(base_result, "retrieval_method")

    def test_search_result_item_inheritance(self):
        """Test that SearchResultItem inherits from RetrievalResultItem."""
        search_result = SearchResultItem(
            content="Test content",
            chunk_id="test_001",
            properties={"content": "Test content", "chunk_id": "test_001"},
            similarity_score=0.8,
            retrieval_method="vector_similarity",
            metadata=RetrievalMetadata(source_document="test.pdf"),
        )

        # Verify it's an instance of both classes
        assert isinstance(search_result, SearchResultItem)
        assert isinstance(search_result, RetrievalResultItem)

        # Verify base class fields are accessible
        assert search_result.content == "Test content"
        assert search_result.chunk_id == "test_001"
        assert search_result.properties["chunk_id"] == "test_001"
        assert search_result.metadata.source_document == "test.pdf"

        # Verify derived class fields are accessible
        assert search_result.similarity_score == 0.8
        assert search_result.retrieval_method == "vector_similarity"

    def test_inheritance_polymorphism(self):
        """Test polymorphism - base class can hold derived instances."""
        search_result = SearchResultItem(
            content="Test content",
            chunk_id="test_001",
            properties={"content": "Test content", "chunk_id": "test_001"},
            similarity_score=0.8,
            retrieval_method="vector_similarity",
            metadata=RetrievalMetadata(source_document="test.pdf"),
        )

        # Can be assigned to base class type
        base_result: RetrievalResultItem = search_result

        # Base class interface works
        assert base_result.content == "Test content"
        assert base_result.chunk_id == "test_001"

        # But still has derived class attributes
        assert base_result.similarity_score == 0.8  # type: ignore
        assert base_result.retrieval_method == "vector_similarity"  # type: ignore

    def test_search_similar_with_filter(
        self, retriever, mock_db_manager, mock_collection, mock_search_result
    ):
        """Test vector similarity search with filter."""
        mock_result = Mock()
        mock_result.objects = [mock_search_result]
        mock_collection.query.near_text.return_value = mock_result
        mock_db_manager.get_collection.return_value = mock_collection

        test_filter = Filter.by_property("chunk_type").equal("text")

        with patch.object(
            retriever, "_preprocess_query", return_value="machine learning"
        ):
            with patch.object(retriever, "_process_vector_results") as mock_process:
                mock_process.return_value = [
                    SearchResultItem(
                        content="test",
                        chunk_id="test_1",
                        similarity_score=0.8,
                        retrieval_method="vector_similarity",
                    )
                ]

                result = retriever.search_similar(
                    "machine learning",
                    collection="Document",
                    top_k=5,
                    filter=test_filter,
                )

                assert len(result) == 1
                mock_collection.query.near_text.assert_called_once_with(
                    query="machine learning",
                    limit=5,
                    return_metadata=MetadataQuery(distance=True),
                    filter=test_filter,
                )

    def test_search_hybrid_with_filter(
        self, retriever, mock_db_manager, mock_collection, mock_search_result
    ):
        """Test hybrid search with filter."""
        mock_result = Mock()
        mock_result.objects = [mock_search_result]
        mock_collection.query.hybrid.return_value = mock_result
        mock_db_manager.get_collection.return_value = mock_collection

        test_filter = Filter.by_property("source_document").equal("test.pdf")

        with patch.object(
            retriever, "_preprocess_query", return_value="machine learning"
        ):
            with patch.object(retriever, "_process_hybrid_results") as mock_process:
                mock_process.return_value = [
                    SearchResultItem(
                        content="test",
                        chunk_id="test_1",
                        similarity_score=0.8,
                        hybrid_score=0.8,
                        retrieval_method="hybrid_search",
                    )
                ]

                result = retriever.search_hybrid(
                    "machine learning",
                    collection="Document",
                    alpha=0.7,
                    top_k=5,
                    filter=test_filter,
                )

                assert len(result) == 1
                mock_collection.query.hybrid.assert_called_once_with(
                    query="machine learning",
                    alpha=0.7,
                    limit=5,
                    return_metadata=MetadataQuery(score=True),
                    filter=test_filter,
                )

    def test_search_keyword_with_filter(
        self, retriever, mock_db_manager, mock_collection, mock_search_result
    ):
        """Test keyword search with filter."""
        mock_result = Mock()
        mock_result.objects = [mock_search_result]
        mock_collection.query.bm25.return_value = mock_result
        mock_db_manager.get_collection.return_value = mock_collection

        test_filter = Filter.by_property("chunk_type").equal("text")

        with patch.object(
            retriever, "_preprocess_query", return_value="machine learning"
        ):
            with patch.object(retriever, "_process_keyword_results") as mock_process:
                mock_process.return_value = [
                    SearchResultItem(
                        content="test",
                        chunk_id="test_1",
                        similarity_score=0.8,
                        bm25_score=0.8,
                        retrieval_method="keyword_search",
                    )
                ]

                result = retriever.search_keyword(
                    "machine learning",
                    collection="Document",
                    top_k=5,
                    filter=test_filter,
                )

                assert len(result) == 1
                mock_collection.query.bm25.assert_called_once_with(
                    query="machine learning",
                    limit=5,
                    return_metadata=MetadataQuery(score=True),
                    filter=test_filter,
                )

    def test_search_with_none_filter(
        self, retriever, mock_db_manager, mock_collection, mock_search_result
    ):
        """Test that None filter works (backward compatibility)."""
        mock_result = Mock()
        mock_result.objects = [mock_search_result]
        mock_collection.query.near_text.return_value = mock_result
        mock_db_manager.get_collection.return_value = mock_collection

        with patch.object(
            retriever, "_preprocess_query", return_value="machine learning"
        ):
            with patch.object(retriever, "_process_vector_results") as mock_process:
                mock_process.return_value = [
                    SearchResultItem(
                        content="test",
                        chunk_id="test_1",
                        similarity_score=0.8,
                        retrieval_method="vector_similarity",
                    )
                ]

                # Explicitly pass None filter
                result = retriever.search_similar(
                    "machine learning", collection="Document", top_k=5, filter=None
                )

                assert len(result) == 1
                mock_collection.query.near_text.assert_called_once_with(
                    query="machine learning",
                    limit=5,
                    return_metadata=MetadataQuery(distance=True),
                    filter=None,
                )
