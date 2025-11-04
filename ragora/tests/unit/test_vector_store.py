"""Unit tests for refactored VectorStore class."""

import json
from unittest.mock import Mock, patch

import pytest
from weaviate.exceptions import WeaviateBaseError

from ragora.core.chunking import ChunkMetadata, DataChunk
from ragora.core.database_manager import DatabaseManager
from ragora.core.embedding_engine import EmbeddingEngine
from ragora.core.models import RetrievalResultItem
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
            collection="TestDocument",
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
            email_subject="Test Email Subject",
            email_sender="test@example.com",
            email_recipient="recipient@example.com",
            email_date="2023-01-01T10:00:00Z",
            email_id="msg123",
            email_folder="inbox",
            custom_metadata={
                "language": "en",
                "domain": "test",
                "confidence": 0.95,
                "tags": ["test", "example"],
                "priority": 3,
                "content_category": "demo",
            },
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
            collection="TestDocument",
            embedding_engine=mock_embedding_engine,
        )

        assert vector_store.db_manager == mock_db_manager
        assert vector_store.collection == "TestDocument"
        assert vector_store.embedding_engine == mock_embedding_engine

    def test_init_without_embedding_engine(self, mock_db_manager):
        """Test initialization without EmbeddingEngine (default None)."""
        vector_store = VectorStore(
            db_manager=mock_db_manager,
            collection="TestDocument",
        )

        # EmbeddingEngine should be None by default (Weaviate handles embeddings)
        assert vector_store.embedding_engine is None

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

        # The method now returns the chunk_key (generated UUID)
        assert isinstance(result, str)
        assert len(result) > 0
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

        # The method now returns a list of chunk_keys (generated UUIDs)
        assert len(result) == 2
        assert all(isinstance(uuid, str) and len(uuid) > 0 for uuid in result)
        mock_db_manager.get_collection.assert_called_once_with("TestDocument")
        assert mock_collection.data.insert.call_count == 2

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
            # Core fields
            "content": "This is a test chunk",
            "chunk_id": "test_chunk_1",
            "chunk_key": "test_chunk_key_uuid",  # This will be generated
            "source_document": "test_doc.pdf",
            "chunk_type": "text",
            "created_at": "2023-01-01T00:00:00",
            # Document-specific fields
            "metadata_chunk_idx": 1,
            "metadata_chunk_size": 100,
            "metadata_total_chunks": 5,
            "metadata_created_at": "2023-01-01T00:00:00",
            "page_number": 1,
            "section_title": "Test Section",
            # Email-specific fields
            "email_subject": "Test Email Subject",
            "email_sender": "test@example.com",
            "email_recipient": "recipient@example.com",
            "email_date": "2023-01-01T10:00:00Z",
            "email_id": "msg123",
            "email_folder": "inbox",
            # Custom metadata fields
            "custom_metadata": '{"language": "en", "domain": "test", "confidence": 0.95, "tags": ["test", "example"], "priority": 3, "content_category": "demo"}',
            "language": "en",
            "domain": "test",
            "confidence": 0.95,
            "tags": "test,example",
            "priority": 3,
            "content_category": "demo",
        }

        # Check all fields except chunk_key which is generated
        for key, value in expected.items():
            if key != "chunk_key":
                assert result[key] == value

        # Check that chunk_key is present and is a string
        assert "chunk_key" in result
        assert isinstance(result["chunk_key"], str)
        assert len(result["chunk_key"]) > 0

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

    def test_prepare_data_object_with_email_fields(self, vector_store):
        """Test prepare_data_object with email metadata."""
        metadata = ChunkMetadata(
            chunk_idx=1,
            chunk_size=50,
            total_chunks=1,
            email_subject="Meeting Notes",
            email_sender="manager@company.com",
            email_recipient="team@company.com",
            email_date="2024-01-15T14:30:00Z",
            email_id="msg_456",
            email_folder="work",
        )
        chunk = DataChunk(
            text="Meeting discussion about project timeline",
            start_idx=0,
            end_idx=50,
            metadata=metadata,
            chunk_id="email_chunk_001",
            source_document="email_001",
            chunk_type="email",
        )

        result = vector_store.prepare_data_object(chunk)

        # Check email fields
        assert result["email_subject"] == "Meeting Notes"
        assert result["email_sender"] == "manager@company.com"
        assert result["email_recipient"] == "team@company.com"
        assert result["email_date"] == "2024-01-15T14:30:00Z"
        assert result["email_id"] == "msg_456"
        assert result["email_folder"] == "work"
        assert result["chunk_type"] == "email"

    def test_prepare_data_object_with_custom_metadata(self, vector_store):
        """Test prepare_data_object with custom metadata JSON serialization."""
        metadata = ChunkMetadata(
            chunk_idx=1,
            chunk_size=50,
            total_chunks=1,
            custom_metadata={
                "language": "es",
                "domain": "legal",
                "confidence": 0.88,
                "tags": ["contract", "agreement"],
                "priority": 5,
                "content_category": "legal_document",
                "custom_field": "special_value",
            },
        )
        chunk = DataChunk(
            text="Contrato de servicios profesionales",
            start_idx=0,
            end_idx=50,
            metadata=metadata,
            chunk_id="custom_chunk_001",
            source_document="contract.pdf",
            chunk_type="document",
        )

        result = vector_store.prepare_data_object(chunk)

        custom_meta = json.loads(result["custom_metadata"])
        assert custom_meta["language"] == "es"
        assert custom_meta["domain"] == "legal"
        assert custom_meta["confidence"] == 0.88
        assert custom_meta["tags"] == ["contract", "agreement"]
        assert custom_meta["priority"] == 5
        assert custom_meta["content_category"] == "legal_document"
        assert custom_meta["custom_field"] == "special_value"

        # Check extracted common fields
        assert result["language"] == "es"
        assert result["domain"] == "legal"
        assert result["confidence"] == 0.88
        assert result["tags"] == "contract,agreement"
        assert result["priority"] == 5
        assert result["content_category"] == "legal_document"

    def test_prepare_data_object_with_custom_metadata_extraction(self, vector_store):
        """Test prepare_data_object with custom metadata extraction edge cases."""
        # Test with empty custom metadata
        metadata = ChunkMetadata(
            chunk_idx=1, chunk_size=50, total_chunks=1, custom_metadata={}
        )
        chunk = DataChunk(
            text="Simple text",
            start_idx=0,
            end_idx=50,
            metadata=metadata,
            chunk_id="empty_custom_001",
            source_document="simple.txt",
            chunk_type="text",
        )

        result = vector_store.prepare_data_object(chunk)

        # Check defaults
        assert result["custom_metadata"] == ""
        assert result["language"] == ""
        assert result["domain"] == ""
        assert result["confidence"] == 0.0
        assert result["tags"] == ""
        assert result["priority"] == 0
        assert result["content_category"] == ""

        # Test with None custom metadata
        metadata.custom_metadata = None
        result = vector_store.prepare_data_object(chunk)
        assert result["custom_metadata"] == ""
        assert result["language"] == ""

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

        mock_collection.query.fetch_object_by_id.return_value = mock_obj
        mock_db_manager.get_collection.return_value = mock_collection

        result = vector_store.get_chunk_by_id("test_chunk_1", "TestDocument")

        assert result is not None
        assert isinstance(result, RetrievalResultItem)
        assert result.content == "test content"
        assert result.chunk_id == "test_chunk_1"
        assert result.properties["source_document"] == "test_doc.pdf"
        assert result.metadata.source_document == "test_doc.pdf"

    def test_get_chunk_by_id_not_found(
        self, vector_store, mock_db_manager, mock_collection
    ):
        """Test chunk retrieval when chunk not found."""
        mock_collection.query.fetch_object_by_id.return_value = None
        mock_db_manager.get_collection.return_value = mock_collection

        result = vector_store.get_chunk_by_id("nonexistent_chunk", "TestDocument")

        assert result is None

    def test_get_chunk_by_id_failure(
        self, vector_store, mock_db_manager, mock_collection
    ):
        """Test chunk retrieval failure."""
        mock_collection.query.fetch_object_by_id.side_effect = WeaviateBaseError(
            "Query failed"
        )
        mock_db_manager.get_collection.return_value = mock_collection

        with pytest.raises(WeaviateBaseError):
            vector_store.get_chunk_by_id("test_chunk_1", "TestDocument")

    def test_get_chunk_by_id_returns_structured_model(
        self, vector_store, mock_db_manager, mock_collection
    ):
        """Test that get_chunk_by_id returns RetrievalResultItem model."""
        mock_obj = Mock()
        mock_obj.properties = {
            "content": "test content",
            "chunk_id": "test_chunk_1",
            "source_document": "test_doc.pdf",
            "chunk_type": "text",
            "metadata_chunk_idx": 1,
            "metadata_chunk_size": 100,
            "metadata_total_chunks": 5,
        }

        mock_collection.query.fetch_object_by_id.return_value = mock_obj
        mock_db_manager.get_collection.return_value = mock_collection

        result = vector_store.get_chunk_by_id("test_chunk_1", "TestDocument")

        assert result is not None
        assert isinstance(result, RetrievalResultItem)
        # Verify all base class fields are accessible
        assert hasattr(result, "content")
        assert hasattr(result, "chunk_id")
        assert hasattr(result, "properties")
        assert hasattr(result, "metadata")
        # Verify metadata is structured
        assert result.metadata is not None

    def test_delete_chunk_success(self, vector_store, mock_db_manager, mock_collection):
        """Test successful chunk deletion."""
        mock_db_manager.get_collection.return_value = mock_collection

        result = vector_store.delete_chunk("test_chunk_1", "TestDocument")

        assert result is True
        mock_collection.data.delete_by_id.assert_called_once()

    def test_delete_chunk_not_found(
        self, vector_store, mock_db_manager, mock_collection
    ):
        """Test chunk deletion when chunk not found."""
        mock_collection.data.delete_by_id.side_effect = WeaviateBaseError("Not found")
        mock_db_manager.get_collection.return_value = mock_collection

        with pytest.raises(WeaviateBaseError):
            vector_store.delete_chunk("nonexistent_chunk", "TestDocument")

    def test_delete_chunk_failure(self, vector_store, mock_db_manager, mock_collection):
        """Test chunk deletion failure."""
        mock_collection.data.delete_by_id.side_effect = WeaviateBaseError(
            "Delete failed"
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
        assert result["collection"] == mock_collection
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
            collection="TestDocument",
            embedding_engine=mock_embedding_engine,
        ) as vector_store:
            assert vector_store.collection == "TestDocument"

        # close should be called when exiting context
        mock_db_manager.close.assert_called_once()

    def test_update_chunk_success(self, vector_store, mock_db_manager, mock_collection):
        """Test successful chunk update."""
        mock_db_manager.get_collection.return_value = mock_collection

        properties = {"content": "Updated content"}
        result = vector_store.update_chunk("test_chunk_1", properties, "TestDocument")

        assert result is True
        mock_collection.data.update_by_id.assert_called_once()

    def test_update_chunk_not_found(
        self, vector_store, mock_db_manager, mock_collection
    ):
        """Test chunk update when chunk not found."""
        mock_collection.data.update_by_id.side_effect = WeaviateBaseError("Not found")
        mock_db_manager.get_collection.return_value = mock_collection

        properties = {"content": "Updated content"}
        with pytest.raises(WeaviateBaseError):
            vector_store.update_chunk("nonexistent_chunk", properties, "TestDocument")

    def test_update_chunk_failure(self, vector_store, mock_db_manager, mock_collection):
        """Test chunk update failure."""
        mock_collection.data.update_by_id.side_effect = WeaviateBaseError(
            "Update failed"
        )
        mock_db_manager.get_collection.return_value = mock_collection

        properties = {"content": "Updated content"}
        with pytest.raises(WeaviateBaseError):
            vector_store.update_chunk("test_chunk_1", properties, "TestDocument")

    def test_chunk_exists_success(self, vector_store, mock_db_manager, mock_collection):
        """Test successful chunk existence check."""
        mock_collection.data.exists.return_value = True
        mock_db_manager.get_collection.return_value = mock_collection

        result = vector_store.chunk_exists("test_chunk_1", "TestDocument")

        assert result is True
        mock_collection.data.exists.assert_called_once()

    def test_chunk_exists_not_found(
        self, vector_store, mock_db_manager, mock_collection
    ):
        """Test chunk existence check when chunk not found."""
        mock_collection.data.exists.return_value = False
        mock_db_manager.get_collection.return_value = mock_collection

        result = vector_store.chunk_exists("nonexistent_chunk", "TestDocument")

        assert result is False

    def test_chunk_exists_failure(self, vector_store, mock_db_manager, mock_collection):
        """Test chunk existence check failure."""
        mock_collection.data.exists.side_effect = WeaviateBaseError(
            "Exists check failed"
        )
        mock_db_manager.get_collection.return_value = mock_collection

        with pytest.raises(WeaviateBaseError):
            vector_store.chunk_exists("test_chunk_1", "TestDocument")
