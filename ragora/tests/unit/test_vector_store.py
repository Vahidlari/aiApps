"""Unit tests for refactored VectorStore class."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from weaviate.exceptions import WeaviateBaseError

from ragora.core.chunking import ChunkMetadata, DataChunk
from ragora.core.database_manager import DatabaseManager
from ragora.core.embedding_engine import EmbeddingEngine
from ragora.core.vector_store import VectorStore


class TestVectorStoreRefactored:
    """Test cases for refactored VectorStore class."""

    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock DatabaseManager."""
        db_manager = Mock(spec=DatabaseManager)
        db_manager.is_connected = True
        db_manager.url = "http://localhost:8080"
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
        return engine

    @pytest.fixture
    def vector_store(self, mock_db_manager, mock_embedding_engine):
        """Create a VectorStore instance with mocked dependencies."""
        return VectorStore(
            db_manager=mock_db_manager,
            class_name="TestDocument",
            embedding_engine=mock_embedding_engine,
        )

    @pytest.fixture
    def sample_chunk(self):
        """Create a sample DataChunk for testing."""
        metadata = ChunkMetadata(
            chunk_idx=1,
            chunk_size=100,
            total_chunks=5,
            created_at="2023-01-01T00:00:00",
            page_number=1,
            section_title="Test Section",
        )
        return DataChunk(
            text="This is a test chunk",
            start_idx=0,
            end_idx=19,
            metadata=metadata,
            chunk_id="test_chunk_1",
            source_document="test_doc.pdf",
            chunk_type="text",
        )

    def test_init_success(self, mock_db_manager, mock_embedding_engine):
        """Test successful initialization of VectorStore."""
        vector_store = VectorStore(
            db_manager=mock_db_manager,
            class_name="TestDocument",
            embedding_engine=mock_embedding_engine,
        )

        assert vector_store.db_manager == mock_db_manager
        assert vector_store.class_name == "TestDocument"
        assert vector_store.embedding_engine == mock_embedding_engine

    def test_init_with_default_embedding_engine(self, mock_db_manager):
        """Test initialization with default EmbeddingEngine."""
        with patch("ragora.core.vector_store.EmbeddingEngine") as mock_engine_class:
            mock_engine = Mock(spec=EmbeddingEngine)
            mock_engine_class.return_value = mock_engine

            vector_store = VectorStore(
                db_manager=mock_db_manager,
                class_name="TestDocument",
            )

            assert vector_store.embedding_engine == mock_engine
            mock_engine_class.assert_called_once()

    def test_init_with_none_db_manager(self):
        """Test initialization with None DatabaseManager."""
        with pytest.raises(ValueError, match="DatabaseManager cannot be None"):
            VectorStore(db_manager=None)

    def test_is_connected(self, vector_store, mock_db_manager):
        """Test is_connected property."""
        mock_db_manager.is_connected = True
        assert vector_store.is_connected() is True

        mock_db_manager.is_connected = False
        assert vector_store.is_connected() is False

    def test_create_schema_success(
        self, vector_store, mock_db_manager, mock_collection
    ):
        """Test successful schema creation."""
        mock_db_manager.collection_exists.return_value = False
        mock_db_manager.create_collection.return_value = mock_collection

        vector_store.create_schema("TestDocument")

        mock_db_manager.collection_exists.assert_called_once_with("TestDocument")
        mock_db_manager.create_collection.assert_called_once()

    def test_create_schema_collection_exists(self, vector_store, mock_db_manager):
        """Test schema creation when collection already exists."""
        mock_db_manager.collection_exists.return_value = True

        vector_store.create_schema("TestDocument")

        mock_db_manager.collection_exists.assert_called_once_with("TestDocument")
        mock_db_manager.create_collection.assert_not_called()

    def test_create_schema_force_recreate(
        self, vector_store, mock_db_manager, mock_collection
    ):
        """Test schema creation with force_recreate=True."""
        mock_db_manager.collection_exists.return_value = True
        mock_db_manager.create_collection.return_value = mock_collection

        vector_store.create_schema("TestDocument", force_recreate=True)

        mock_db_manager.collection_exists.assert_called_once_with("TestDocument")
        mock_db_manager.delete_collection.assert_called_once_with("TestDocument")
        mock_db_manager.create_collection.assert_called_once()

    def test_create_schema_failure(self, vector_store, mock_db_manager):
        """Test schema creation failure."""
        mock_db_manager.collection_exists.return_value = False
        mock_db_manager.create_collection.side_effect = WeaviateBaseError(
            "Creation failed"
        )

        with pytest.raises(WeaviateBaseError):
            vector_store.create_schema("TestDocument")

    def test_store_chunk_success(
        self, vector_store, mock_db_manager, mock_collection, sample_chunk
    ):
        """Test successful chunk storage."""
        mock_db_manager.get_collection.return_value = mock_collection
        mock_collection.data.insert.return_value = "test_uuid"

        with patch.object(vector_store, "create_schema"):
            result = vector_store.store_chunk(sample_chunk, "TestDocument")

        assert result == "test_uuid"
        mock_db_manager.get_collection.assert_called_once_with("TestDocument")
        mock_collection.data.insert.assert_called_once()

    def test_store_chunk_none_chunk(self, vector_store):
        """Test store_chunk with None chunk."""
        with pytest.raises(ValueError, match="Chunk cannot be None"):
            vector_store.store_chunk(None, "TestDocument")

    def test_store_chunk_empty_text(self, vector_store, sample_chunk):
        """Test store_chunk with empty text."""
        sample_chunk.text = ""

        with pytest.raises(ValueError, match="Chunk text cannot be empty"):
            vector_store.store_chunk(sample_chunk, "TestDocument")

    def test_store_chunk_storage_failure(
        self, vector_store, mock_db_manager, mock_collection, sample_chunk
    ):
        """Test store_chunk storage failure."""
        mock_db_manager.get_collection.return_value = mock_collection
        mock_collection.data.insert.side_effect = WeaviateBaseError("Storage failed")

        with patch.object(vector_store, "create_schema"):
            with pytest.raises(WeaviateBaseError):
                vector_store.store_chunk(sample_chunk, "TestDocument")

    def test_store_chunks_success(
        self, vector_store, mock_db_manager, mock_collection, sample_chunk
    ):
        """Test successful chunk batch storage."""
        chunks = [sample_chunk, sample_chunk]
        mock_db_manager.get_collection.return_value = mock_collection
        mock_collection.data.insert.return_value = "test_uuid"

        with patch.object(vector_store, "create_schema"):
            result = vector_store.store_chunks(chunks, "TestDocument", batch_size=1)

        assert len(result) == 2
        assert all(uuid == "test_uuid" for uuid in result)

    def test_store_chunks_empty_list(self, vector_store):
        """Test store_chunks with empty list."""
        with pytest.raises(ValueError, match="Chunks list cannot be empty"):
            vector_store.store_chunks([], "TestDocument")

    def test_store_chunks_no_valid_chunks(self, vector_store, sample_chunk):
        """Test store_chunks with no valid chunks."""
        sample_chunk.text = ""
        chunks = [sample_chunk]

        with pytest.raises(ValueError, match="No valid chunks found in the list"):
            vector_store.store_chunks(chunks, "TestDocument")

    def test_prepare_data_object(self, vector_store, sample_chunk):
        """Test prepare_data_object method."""
        result = vector_store.prepare_data_object(sample_chunk)

        expected = {
            "content": "This is a test chunk",
            "chunk_id": "test_chunk_1",
            "source_document": "test_doc.pdf",
            "chunk_type": "text",
            "metadata_chunk_idx": 1,
            "metadata_chunk_size": 100,
            "metadata_total_chunks": 5,
            "metadata_created_at": "2023-01-01T00:00:00",
            "page_number": 1,
            "section_title": "Test Section",
        }

        assert result == expected

    def test_prepare_data_object_none_chunk(self, vector_store):
        """Test prepare_data_object with None chunk."""
        with pytest.raises(ValueError, match="Chunk cannot be None"):
            vector_store.prepare_data_object(None)

    def test_prepare_data_object_empty_text(self, vector_store, sample_chunk):
        """Test prepare_data_object with empty text."""
        sample_chunk.text = ""

        with pytest.raises(ValueError, match="Chunk text cannot be empty"):
            vector_store.prepare_data_object(sample_chunk)

    def test_prepare_data_object_empty_chunk_id(self, vector_store, sample_chunk):
        """Test prepare_data_object with empty chunk_id."""
        sample_chunk.chunk_id = ""

        with pytest.raises(ValueError, match="Chunk ID cannot be empty"):
            vector_store.prepare_data_object(sample_chunk)

    def test_get_chunk_by_id_success(
        self, vector_store, mock_db_manager, mock_collection
    ):
        """Test successful chunk retrieval by ID."""
        mock_obj = Mock()
        mock_obj.properties = {
            "content": "test content",
            "chunk_id": "test_chunk_1",
            "source_document": "test_doc.pdf",
            "chunk_type": "text",
            "metadata_chunk_idx": 1,
            "metadata_chunk_size": 100,
            "metadata_total_chunks": 5,
            "metadata_created_at": "2023-01-01T00:00:00",
            "page_number": 1,
            "section_title": "Test Section",
        }

        mock_result = Mock()
        mock_result.objects = [mock_obj]
        mock_collection.query.fetch_objects.return_value = mock_result
        mock_db_manager.get_collection.return_value = mock_collection

        result = vector_store.get_chunk_by_id("test_chunk_1", "TestDocument")

        assert result is not None
        assert result["content"] == "test content"
        assert result["chunk_id"] == "test_chunk_1"

    def test_get_chunk_by_id_not_found(
        self, vector_store, mock_db_manager, mock_collection
    ):
        """Test chunk retrieval when chunk not found."""
        mock_result = Mock()
        mock_result.objects = []
        mock_collection.query.fetch_objects.return_value = mock_result
        mock_db_manager.get_collection.return_value = mock_collection

        result = vector_store.get_chunk_by_id("nonexistent_chunk", "TestDocument")

        assert result is None

    def test_get_chunk_by_id_failure(
        self, vector_store, mock_db_manager, mock_collection
    ):
        """Test chunk retrieval failure."""
        mock_collection.query.fetch_objects.side_effect = WeaviateBaseError(
            "Query failed"
        )
        mock_db_manager.get_collection.return_value = mock_collection

        with pytest.raises(WeaviateBaseError):
            vector_store.get_chunk_by_id("test_chunk_1", "TestDocument")

    def test_delete_chunk_success(self, vector_store, mock_db_manager, mock_collection):
        """Test successful chunk deletion."""
        mock_obj = Mock()
        mock_obj.uuid = "test_uuid"
        mock_result = Mock()
        mock_result.objects = [mock_obj]
        mock_collection.query.fetch_objects.return_value = mock_result
        mock_db_manager.get_collection.return_value = mock_collection

        result = vector_store.delete_chunk("test_chunk_1", "TestDocument")

        assert result is True
        mock_collection.data.delete_by_id.assert_called_once_with("test_uuid")

    def test_delete_chunk_not_found(
        self, vector_store, mock_db_manager, mock_collection
    ):
        """Test chunk deletion when chunk not found."""
        mock_result = Mock()
        mock_result.objects = []
        mock_collection.query.fetch_objects.return_value = mock_result
        mock_db_manager.get_collection.return_value = mock_collection

        result = vector_store.delete_chunk("nonexistent_chunk", "TestDocument")

        assert result is False

    def test_delete_chunk_failure(self, vector_store, mock_db_manager, mock_collection):
        """Test chunk deletion failure."""
        mock_collection.query.fetch_objects.side_effect = WeaviateBaseError(
            "Query failed"
        )
        mock_db_manager.get_collection.return_value = mock_collection

        with pytest.raises(WeaviateBaseError):
            vector_store.delete_chunk("test_chunk_1", "TestDocument")

    def test_get_stats_success(self, vector_store, mock_db_manager, mock_collection):
        """Test successful stats retrieval."""
        mock_result = Mock()
        mock_result.total_count = 100
        mock_collection.aggregate.over_all.return_value = mock_result
        mock_collection.name = "TestDocument"
        mock_collection.config = Mock()
        mock_collection.config.description = "Test collection"
        mock_collection.config.vectorizer_config = None
        mock_db_manager.get_collection.return_value = mock_collection

        result = vector_store.get_stats("TestDocument")

        assert result["total_objects"] == 100
        assert result["class_name"] == "TestDocument"
        assert result["is_connected"] is True
        assert result["db_manager_url"] == "http://localhost:8080"

    def test_get_stats_failure(self, vector_store, mock_db_manager, mock_collection):
        """Test stats retrieval failure."""
        mock_collection.aggregate.over_all.side_effect = WeaviateBaseError(
            "Stats failed"
        )
        mock_db_manager.get_collection.return_value = mock_collection

        with pytest.raises(WeaviateBaseError):
            vector_store.get_stats("TestDocument")

    def test_clear_all_success(self, vector_store, mock_db_manager):
        """Test successful clearing of all objects."""
        vector_store.clear_all("TestDocument")

        mock_db_manager.delete_collection.assert_called_once_with("TestDocument")

    def test_clear_all_failure(self, vector_store, mock_db_manager):
        """Test clear_all failure."""
        mock_db_manager.delete_collection.side_effect = WeaviateBaseError(
            "Clear failed"
        )

        with pytest.raises(WeaviateBaseError):
            vector_store.clear_all("TestDocument")

    def test_close(self, vector_store, mock_db_manager):
        """Test close method."""
        vector_store.close()

        mock_db_manager.close.assert_called_once()

    def test_context_manager(self, mock_db_manager, mock_embedding_engine):
        """Test VectorStore as context manager."""
        with VectorStore(
            db_manager=mock_db_manager,
            class_name="TestDocument",
            embedding_engine=mock_embedding_engine,
        ) as vector_store:
            assert vector_store.class_name == "TestDocument"

        # close should be called when exiting context
        mock_db_manager.close.assert_called_once()
