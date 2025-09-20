"""Unit tests for the refactored VectorStore module.

This module contains comprehensive unit tests for the refactored VectorStore class,
focusing on storage operations and internal methods used by the Retriever.

Test coverage includes:
- Connection initialization and error handling
- Schema creation and management
- Document storage operations (single and batch)
- CRUD operations (get, delete)
- Internal search methods for Retriever
- Error conditions and edge cases
- Context manager functionality
- Statistics and monitoring
"""

from unittest.mock import Mock, patch

import pytest
from core.data_chunker import ChunkMetadata, DataChunk
from core.embedding_engine import EmbeddingEngine
from core.vector_store import VectorStore
from weaviate.exceptions import WeaviateBaseError


class TestVectorStoreRefactored:
    """Test suite for refactored VectorStore class."""

    @pytest.fixture
    def mock_weaviate_client(self):
        """Create a mock Weaviate client."""
        mock_client = Mock()
        mock_client.is_ready.return_value = True
        mock_client.schema.get.return_value = {"classes": []}
        return mock_client

    @pytest.fixture
    def mock_embedding_engine(self):
        """Create a mock embedding engine."""
        mock_engine = Mock(spec=EmbeddingEngine)
        mock_engine.model_name = "all-mpnet-base-v2"
        mock_engine.embedding_dimension = 768
        return mock_engine

    @pytest.fixture
    def sample_chunk(self):
        """Create a sample DataChunk for testing."""
        return DataChunk(
            text="This is a test document chunk with some content.",
            start_idx=0,
            end_idx=50,
            metadata=ChunkMetadata(
                chunk_id=1,
                chunk_size=50,
                total_chunks=1,
                source_document="test_document.tex",
                page_number=1,
                section_title="Introduction",
                chunk_type="text",
            ),
            chunk_id="test_chunk_001",
            source_document="test_document.tex",
            chunk_type="text",
        )

    @pytest.fixture
    def sample_chunks(self):
        """Create multiple sample DataChunks for testing."""
        return [
            DataChunk(
                text="First test chunk with mathematical content: E = mc²",
                start_idx=0,
                end_idx=50,
                metadata=ChunkMetadata(
                    chunk_id=1,
                    chunk_size=50,
                    total_chunks=3,
                    source_document="test_document.tex",
                    page_number=1,
                    section_title="Introduction",
                    chunk_type="text",
                ),
                chunk_id="test_chunk_001",
                source_document="test_document.tex",
                chunk_type="text",
            ),
            DataChunk(
                text="Second test chunk with citation: Einstein (1905)",
                start_idx=51,
                end_idx=100,
                metadata=ChunkMetadata(
                    chunk_id=2,
                    chunk_size=49,
                    total_chunks=3,
                    source_document="test_document.tex",
                    page_number=2,
                    section_title="Background",
                    chunk_type="citation",
                ),
                chunk_id="test_chunk_002",
                source_document="test_document.tex",
                chunk_type="citation",
            ),
            DataChunk(
                text="Third test chunk with equation: F = ma",
                start_idx=101,
                end_idx=150,
                metadata=ChunkMetadata(
                    chunk_id=3,
                    chunk_size=49,
                    total_chunks=3,
                    source_document="test_document.tex",
                    page_number=3,
                    section_title="Methods",
                    chunk_type="equation",
                ),
                chunk_id="test_chunk_003",
                source_document="test_document.tex",
                chunk_type="equation",
            ),
        ]

    @patch("core.vector_store.Client")
    def test_vector_store_initialization_success(
        self, mock_client_class, mock_weaviate_client, mock_embedding_engine
    ):
        """Test successful VectorStore initialization."""
        # Setup
        mock_client_class.return_value = mock_weaviate_client

        # Test
        vector_store = VectorStore(
            url="http://localhost:8080",
            class_name="TestDocument",
            embedding_engine=mock_embedding_engine,
        )

        # Assertions
        assert vector_store.url == "http://localhost:8080"
        assert vector_store.class_name == "TestDocument"
        assert vector_store.embedding_engine == mock_embedding_engine
        assert vector_store.is_connected is True
        mock_client_class.assert_called_once_with(
            "http://localhost:8080", timeout_config=(60, 60)
        )

    @patch("core.vector_store.Client")
    def test_vector_store_initialization_with_default_embedding_engine(
        self, mock_client_class, mock_weaviate_client
    ):
        """Test VectorStore initialization with default embedding engine."""
        # Setup
        mock_client_class.return_value = mock_weaviate_client

        with patch("core.vector_store.EmbeddingEngine") as mock_embedding_class:
            mock_embedding_engine = Mock()
            mock_embedding_class.return_value = mock_embedding_engine

            # Test
            vector_store = VectorStore()

            # Assertions
            assert vector_store.embedding_engine == mock_embedding_engine
            mock_embedding_class.assert_called_once()

    @patch("core.vector_store.Client")
    def test_vector_store_initialization_connection_failure(self, mock_client_class):
        """Test VectorStore initialization with connection failure."""
        # Setup
        mock_client_class.side_effect = Exception("Connection failed")

        # Test & Assertions
        with pytest.raises(ConnectionError, match="Could not connect to Weaviate"):
            VectorStore()

    @patch("core.vector_store.Client")
    def test_vector_store_initialization_weaviate_not_ready(self, mock_client_class):
        """Test VectorStore initialization when Weaviate is not ready."""
        # Setup
        mock_client = Mock()
        mock_client.is_ready.return_value = False
        mock_client_class.return_value = mock_client

        # Test & Assertions
        with pytest.raises(ConnectionError, match="Weaviate is not ready"):
            VectorStore()

    @patch("core.vector_store.Client")
    def test_create_schema_success(
        self, mock_client_class, mock_weaviate_client, mock_embedding_engine
    ):
        """Test successful schema creation."""
        # Setup
        mock_client_class.return_value = mock_weaviate_client
        vector_store = VectorStore(embedding_engine=mock_embedding_engine)

        # Test
        vector_store.create_schema()

        # Assertions
        mock_weaviate_client.schema.create_class.assert_called_once()
        call_args = mock_weaviate_client.schema.create_class.call_args[0][0]
        assert call_args["class"] == "Document"
        assert call_args["vectorizer"] == "text2vec-transformers"
        assert "content" in [prop["name"] for prop in call_args["properties"]]

    @patch("core.vector_store.Client")
    def test_create_schema_already_exists(
        self, mock_client_class, mock_weaviate_client, mock_embedding_engine
    ):
        """Test schema creation when schema already exists."""
        # Setup
        mock_client_class.return_value = mock_weaviate_client
        mock_weaviate_client.schema.get.return_value = {
            "classes": [{"class": "Document"}]
        }
        vector_store = VectorStore(embedding_engine=mock_embedding_engine)

        # Test
        vector_store.create_schema()

        # Assertions
        mock_weaviate_client.schema.create_class.assert_not_called()

    @patch("core.vector_store.Client")
    def test_create_schema_force_recreate(
        self, mock_client_class, mock_weaviate_client, mock_embedding_engine
    ):
        """Test schema creation with force_recreate=True."""
        # Setup
        mock_client_class.return_value = mock_weaviate_client
        mock_weaviate_client.schema.get.return_value = {
            "classes": [{"class": "Document"}]
        }
        vector_store = VectorStore(embedding_engine=mock_embedding_engine)

        # Test
        vector_store.create_schema(force_recreate=True)

        # Assertions
        mock_weaviate_client.schema.delete_class.assert_called_once_with("Document")
        mock_weaviate_client.schema.create_class.assert_called_once()

    @patch("core.vector_store.Client")
    def test_store_chunk_success(
        self,
        mock_client_class,
        mock_weaviate_client,
        mock_embedding_engine,
        sample_chunk,
    ):
        """Test successful chunk storage."""
        # Setup
        mock_client_class.return_value = mock_weaviate_client
        mock_weaviate_client.data_object.create.return_value = "test-uuid-123"
        vector_store = VectorStore(embedding_engine=mock_embedding_engine)

        # Test
        result_uuid = vector_store.store_chunk(sample_chunk)

        # Assertions
        assert result_uuid == "test-uuid-123"
        mock_weaviate_client.data_object.create.assert_called_once()
        call_args = mock_weaviate_client.data_object.create.call_args
        assert call_args[1]["class_name"] == "Document"
        assert call_args[1]["data_object"]["content"] == sample_chunk.text
        assert call_args[1]["data_object"]["chunk_id"] == sample_chunk.chunk_id

    @patch("core.vector_store.Client")
    def test_store_chunk_invalid_chunk(
        self, mock_client_class, mock_weaviate_client, mock_embedding_engine
    ):
        """Test chunk storage with invalid chunk."""
        # Setup
        mock_client_class.return_value = mock_weaviate_client
        vector_store = VectorStore(embedding_engine=mock_embedding_engine)

        # Test & Assertions
        with pytest.raises(ValueError, match="Chunk cannot be None"):
            vector_store.store_chunk(None)

        with pytest.raises(ValueError, match="Chunk text cannot be empty"):
            empty_chunk = DataChunk(
                text="",
                start_idx=0,
                end_idx=0,
                metadata=ChunkMetadata(
                    chunk_id=1,
                    chunk_size=0,
                    total_chunks=1,
                    source_document="test.tex",
                    chunk_type="text",
                ),
                chunk_id="empty",
                source_document="test.tex",
                chunk_type="text",
            )
            vector_store.store_chunk(empty_chunk)

    @patch("core.vector_store.Client")
    def test_store_chunks_success(
        self,
        mock_client_class,
        mock_weaviate_client,
        mock_embedding_engine,
        sample_chunks,
    ):
        """Test successful batch chunk storage."""
        # Setup
        mock_client_class.return_value = mock_weaviate_client
        mock_batch_result = [
            Mock(result={"id": "uuid-1"}),
            Mock(result={"id": "uuid-2"}),
            Mock(result={"id": "uuid-3"}),
        ]
        mock_weaviate_client.batch.create_objects.return_value = mock_batch_result
        vector_store = VectorStore(embedding_engine=mock_embedding_engine)

        # Test
        result_uuids = vector_store.store_chunks(sample_chunks, batch_size=3)

        # Assertions
        assert len(result_uuids) == 3
        assert result_uuids == ["uuid-1", "uuid-2", "uuid-3"]
        mock_weaviate_client.batch.create_objects.assert_called()

    @patch("core.vector_store.Client")
    def test_store_chunks_empty_list(
        self, mock_client_class, mock_weaviate_client, mock_embedding_engine
    ):
        """Test batch chunk storage with empty list."""
        # Setup
        mock_client_class.return_value = mock_weaviate_client
        vector_store = VectorStore(embedding_engine=mock_embedding_engine)

        # Test & Assertions
        with pytest.raises(ValueError, match="Chunks list cannot be empty"):
            vector_store.store_chunks([])

    @patch("core.vector_store.Client")
    def test_get_chunk_by_id_success(
        self, mock_client_class, mock_weaviate_client, mock_embedding_engine
    ):
        """Test successful chunk retrieval by ID."""
        # Setup
        mock_client_class.return_value = mock_weaviate_client
        mock_query_result = {
            "data": {
                "Get": {
                    "Document": [
                        {
                            "content": "Retrieved content",
                            "chunk_id": "test_001",
                            "source_document": "test.tex",
                            "chunk_type": "text",
                            "metadata": {"page": 1},
                            "page_number": 1,
                            "section_title": "Test",
                        }
                    ]
                }
            }
        }
        mock_weaviate_client.query.get.return_value.with_where.return_value.with_limit.return_value.do.return_value = (
            mock_query_result
        )
        vector_store = VectorStore(embedding_engine=mock_embedding_engine)

        # Test
        result = vector_store.get_chunk_by_id("test_001")

        # Assertions
        assert result is not None
        assert result["content"] == "Retrieved content"
        assert result["chunk_id"] == "test_001"

    @patch("core.vector_store.Client")
    def test_get_chunk_by_id_not_found(
        self, mock_client_class, mock_weaviate_client, mock_embedding_engine
    ):
        """Test chunk retrieval by ID when chunk is not found."""
        # Setup
        mock_client_class.return_value = mock_weaviate_client
        mock_query_result = {"data": {"Get": {"Document": []}}}
        mock_weaviate_client.query.get.return_value.with_where.return_value.with_limit.return_value.do.return_value = (
            mock_query_result
        )
        vector_store = VectorStore(embedding_engine=mock_embedding_engine)

        # Test
        result = vector_store.get_chunk_by_id("nonexistent")

        # Assertions
        assert result is None

    @patch("core.vector_store.Client")
    def test_delete_chunk_success(
        self, mock_client_class, mock_weaviate_client, mock_embedding_engine
    ):
        """Test successful chunk deletion."""
        # Setup
        mock_client_class.return_value = mock_weaviate_client
        mock_query_result = {
            "data": {
                "Get": {
                    "Document": [
                        {
                            "chunk_id": "test_001",
                            "_additional": {"id": "weaviate-uuid-123"},
                        }
                    ]
                }
            }
        }
        mock_weaviate_client.query.get.return_value.with_where.return_value.with_additional.return_value.with_limit.return_value.do.return_value = (
            mock_query_result
        )
        vector_store = VectorStore(embedding_engine=mock_embedding_engine)

        # Test
        result = vector_store.delete_chunk("test_001")

        # Assertions
        assert result is True
        mock_weaviate_client.data_object.delete.assert_called_once_with(
            uuid="weaviate-uuid-123", class_name="Document"
        )

    @patch("core.vector_store.Client")
    def test_delete_chunk_not_found(
        self, mock_client_class, mock_weaviate_client, mock_embedding_engine
    ):
        """Test chunk deletion when chunk is not found."""
        # Setup
        mock_client_class.return_value = mock_weaviate_client
        mock_query_result = {"data": {"Get": {"Document": []}}}
        mock_weaviate_client.query.get.return_value.with_where.return_value.with_additional.return_value.with_limit.return_value.do.return_value = (
            mock_query_result
        )
        vector_store = VectorStore(embedding_engine=mock_embedding_engine)

        # Test
        result = vector_store.delete_chunk("nonexistent")

        # Assertions
        assert result is False
        mock_weaviate_client.data_object.delete.assert_not_called()

    @patch("core.vector_store.Client")
    def test_get_stats_success(
        self, mock_client_class, mock_weaviate_client, mock_embedding_engine
    ):
        """Test successful stats retrieval."""
        # Setup
        mock_client_class.return_value = mock_weaviate_client
        mock_aggregate_result = {
            "data": {"Aggregate": {"Document": [{"meta": {"count": 42}}]}}
        }
        mock_schema_result = {
            "classes": [{"class": "Document", "description": "Test class"}]
        }
        mock_weaviate_client.query.aggregate.return_value.with_meta_count.return_value.do.return_value = (
            mock_aggregate_result
        )
        mock_weaviate_client.schema.get.return_value = mock_schema_result
        vector_store = VectorStore(embedding_engine=mock_embedding_engine)

        # Test
        stats = vector_store.get_stats()

        # Assertions
        assert stats["total_objects"] == 42
        assert stats["class_name"] == "Document"
        assert stats["is_connected"] is True
        assert stats["url"] == "http://localhost:8080"

    @patch("core.vector_store.Client")
    def test_clear_all_success(
        self, mock_client_class, mock_weaviate_client, mock_embedding_engine
    ):
        """Test successful clearing of all objects."""
        # Setup
        mock_client_class.return_value = mock_weaviate_client
        vector_store = VectorStore(embedding_engine=mock_embedding_engine)

        # Test
        vector_store.clear_all()

        # Assertions
        mock_weaviate_client.schema.delete_class.assert_called_once_with("Document")

    @patch("core.vector_store.Client")
    def test_context_manager(
        self, mock_client_class, mock_weaviate_client, mock_embedding_engine
    ):
        """Test VectorStore as context manager."""
        # Setup
        mock_client_class.return_value = mock_weaviate_client

        # Test
        with VectorStore(embedding_engine=mock_embedding_engine) as vector_store:
            assert vector_store.is_connected is True

        # Assertions
        assert vector_store.is_connected is False

    # Internal methods tests (used by Retriever)
    @patch("core.vector_store.Client")
    def test_search_similar_internal_success(
        self, mock_client_class, mock_weaviate_client, mock_embedding_engine
    ):
        """Test successful internal vector similarity search."""
        # Setup
        mock_client_class.return_value = mock_weaviate_client
        mock_query_result = {
            "data": {
                "Get": {
                    "Document": [
                        {
                            "content": "Test content",
                            "chunk_id": "test_001",
                            "source_document": "test.tex",
                            "chunk_type": "text",
                            "metadata": {"page": 1},
                            "page_number": 1,
                            "section_title": "Test",
                            "_additional": {
                                "certainty": 0.85,
                                "distance": 0.15,
                            },
                        }
                    ]
                }
            }
        }
        mock_weaviate_client.query.get.return_value.with_near_text.return_value.with_limit.return_value.with_additional.return_value.do.return_value = (
            mock_query_result
        )
        vector_store = VectorStore(embedding_engine=mock_embedding_engine)

        # Test
        results = vector_store._search_similar_internal("test query", top_k=5)

        # Assertions
        assert len(results) == 1
        assert results[0]["content"] == "Test content"
        assert results[0]["similarity_score"] == 0.85
        assert results[0]["chunk_id"] == "test_001"

    @patch("core.vector_store.Client")
    def test_search_hybrid_internal_success(
        self, mock_client_class, mock_weaviate_client, mock_embedding_engine
    ):
        """Test successful internal hybrid search."""
        # Setup
        mock_client_class.return_value = mock_weaviate_client
        mock_query_result = {
            "data": {
                "Get": {
                    "Document": [
                        {
                            "content": "Hybrid test content",
                            "chunk_id": "hybrid_001",
                            "source_document": "test.tex",
                            "chunk_type": "text",
                            "metadata": {"page": 1},
                            "page_number": 1,
                            "section_title": "Test",
                            "_additional": {"score": 0.92},
                        }
                    ]
                }
            }
        }
        mock_weaviate_client.query.get.return_value.with_hybrid.return_value.with_limit.return_value.with_additional.return_value.do.return_value = (
            mock_query_result
        )
        vector_store = VectorStore(embedding_engine=mock_embedding_engine)

        # Test
        results = vector_store._search_hybrid_internal(
            "hybrid query", alpha=0.7, top_k=3
        )

        # Assertions
        assert len(results) == 1
        assert results[0]["content"] == "Hybrid test content"
        assert results[0]["hybrid_score"] == 0.92
        assert results[0]["chunk_id"] == "hybrid_001"

    @patch("core.vector_store.Client")
    def test_build_where_filter(
        self, mock_client_class, mock_weaviate_client, mock_embedding_engine
    ):
        """Test where filter building."""
        # Setup
        mock_client_class.return_value = mock_weaviate_client
        vector_store = VectorStore(embedding_engine=mock_embedding_engine)

        # Test string filter
        string_filter = vector_store._build_where_filter({"chunk_type": "text"})
        assert string_filter["path"] == ["chunk_type"]
        assert string_filter["operator"] == "Equal"
        assert string_filter["valueString"] == "text"

        # Test int filter
        int_filter = vector_store._build_where_filter({"page_number": 1})
        assert int_filter["path"] == ["page_number"]
        assert int_filter["operator"] == "Equal"
        assert int_filter["valueInt"] == 1

        # Test list filter
        list_filter = vector_store._build_where_filter(
            {"chunk_type": ["text", "citation"]}
        )
        assert list_filter["path"] == ["chunk_type"]
        assert list_filter["operator"] == "ContainsAny"
        assert list_filter["valueStringArray"] == ["text", "citation"]

        # Test multiple filters
        multi_filter = vector_store._build_where_filter(
            {"chunk_type": "text", "page_number": 1}
        )
        assert multi_filter["operator"] == "And"
        assert len(multi_filter["operands"]) == 2

        # Test empty filter
        empty_filter = vector_store._build_where_filter({})
        assert empty_filter is None

    @patch("core.vector_store.Client")
    def test_weaviate_error_handling(
        self,
        mock_client_class,
        mock_weaviate_client,
        mock_embedding_engine,
        sample_chunk,
    ):
        """Test Weaviate error handling."""
        # Setup
        mock_client_class.return_value = mock_weaviate_client
        mock_weaviate_client.data_object.create.side_effect = WeaviateBaseError(
            "Weaviate error"
        )
        vector_store = VectorStore(embedding_engine=mock_embedding_engine)

        # Test & Assertions
        with pytest.raises(WeaviateBaseError, match="Weaviate error"):
            vector_store.store_chunk(sample_chunk)

    def test_embedding_engine_integration(self, mock_embedding_engine):
        """Test integration with EmbeddingEngine."""
        # Setup
        mock_embedding_engine.model_name = "test-model"
        mock_embedding_engine.embedding_dimension = 512

        with patch("core.vector_store.Client") as mock_client_class:
            mock_client = Mock()
            mock_client.is_ready.return_value = True
            mock_client.schema.get.return_value = {"classes": []}
            mock_client_class.return_value = mock_client

            # Test
            vector_store = VectorStore(embedding_engine=mock_embedding_engine)

            # Assertions
            assert vector_store.embedding_engine == mock_embedding_engine
            assert vector_store.embedding_engine.model_name == "test-model"

    @patch("core.vector_store.Client")
    def test_close_connection(
        self, mock_client_class, mock_weaviate_client, mock_embedding_engine
    ):
        """Test connection closure."""
        # Setup
        mock_client_class.return_value = mock_weaviate_client
        vector_store = VectorStore(embedding_engine=mock_embedding_engine)

        # Test
        vector_store.close()

        # Assertions
        assert vector_store.is_connected is False

    @patch("core.vector_store.Client")
    def test_close_without_client(
        self, mock_client_class, mock_weaviate_client, mock_embedding_engine
    ):
        """Test connection closure without client."""
        # Setup
        mock_client_class.return_value = mock_weaviate_client
        vector_store = VectorStore(embedding_engine=mock_embedding_engine)
        del vector_store.client  # Remove client attribute

        # Test (should not raise exception)
        vector_store.close()

        # Assertions
        # is_connected should still be True since there was no client to close
        assert vector_store.is_connected is True
