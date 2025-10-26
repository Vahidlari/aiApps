"""Unit tests for DatabaseManager class."""

from unittest.mock import Mock, patch

import pytest
from weaviate.exceptions import WeaviateBaseError

from ragora.core.database_manager import DatabaseManager


class TestDatabaseManager:
    """Test cases for DatabaseManager class."""

    @pytest.fixture
    def mock_weaviate_client(self):
        """Create a mock Weaviate client."""
        client = Mock()
        client.is_ready.return_value = True
        client.collections.list_all.return_value = {}
        return client

    @pytest.fixture
    def mock_connection_params(self):
        """Create mock connection parameters."""
        with patch("ragora.core.database_manager.ConnectionParams") as mock:
            mock.from_url.return_value = Mock()
            yield mock

    @pytest.fixture
    def database_manager(self, mock_weaviate_client, mock_connection_params):
        """Create a DatabaseManager instance with mocked dependencies."""
        with patch("ragora.core.database_manager.WeaviateClient") as mock_client_class:
            mock_client_class.return_value = mock_weaviate_client
            db_manager = DatabaseManager(
                url="http://localhost:8080",
                grpc_port=50051,
                timeout=60,
                retry_attempts=3,
            )
            db_manager.client = mock_weaviate_client
            return db_manager

    def test_init_success(self, mock_weaviate_client, mock_connection_params):
        """Test successful initialization of DatabaseManager."""
        with patch("ragora.core.database_manager.WeaviateClient") as mock_client_class:
            mock_client_class.return_value = mock_weaviate_client

            db_manager = DatabaseManager(
                url="http://localhost:8080",
                grpc_port=50051,
                timeout=60,
                retry_attempts=3,
            )

            assert db_manager.url == "http://localhost:8080"
            assert db_manager.grpc_port == 50051
            assert db_manager.timeout == 60
            assert db_manager.retry_attempts == 3
            assert db_manager.is_connected is True
            mock_weaviate_client.connect.assert_called_once()
            mock_weaviate_client.is_ready.assert_called()

    def test_init_connection_failure(self, mock_connection_params):
        """Test initialization failure when connection fails."""
        with patch("ragora.core.database_manager.WeaviateClient") as mock_client_class:
            mock_client = Mock()
            mock_client.connect.side_effect = Exception("Connection failed")
            mock_client_class.return_value = mock_client

            with pytest.raises(ConnectionError, match="Could not connect to Weaviate"):
                DatabaseManager(url="http://localhost:8080")

    def test_test_connection_success(self, database_manager, mock_weaviate_client):
        """Test successful connection test."""
        result = database_manager._test_connection()
        assert result is True
        assert database_manager.is_connected is True
        mock_weaviate_client.is_ready.assert_called()
        mock_weaviate_client.collections.list_all.assert_called()

    def test_test_connection_not_ready(self, database_manager, mock_weaviate_client):
        """Test connection test when Weaviate is not ready."""
        mock_weaviate_client.is_ready.return_value = False

        with pytest.raises(ConnectionError, match="Weaviate is not ready"):
            database_manager._test_connection()

    def test_test_connection_failure(self, database_manager, mock_weaviate_client):
        """Test connection test failure."""
        mock_weaviate_client.collections.list_all.side_effect = Exception("Test failed")

        with pytest.raises(ConnectionError, match="Connection test failed"):
            database_manager._test_connection()

    def test_is_ready_success(self, database_manager, mock_weaviate_client):
        """Test is_ready method when database is ready."""
        mock_weaviate_client.is_ready.return_value = True
        result = database_manager.is_ready()
        assert result is True

    def test_is_ready_failure(self, database_manager, mock_weaviate_client):
        """Test is_ready method when database is not ready."""
        mock_weaviate_client.is_ready.side_effect = Exception("Not ready")
        result = database_manager.is_ready()
        assert result is False

    def test_get_collection_success(self, database_manager, mock_weaviate_client):
        """Test successful collection retrieval."""
        mock_collection = Mock()
        mock_weaviate_client.collections.get.return_value = mock_collection

        result = database_manager.get_collection("test_collection")

        assert result == mock_collection
        # Name should be normalized (first letter capitalized)
        mock_weaviate_client.collections.get.assert_called_once_with("Test_collection")

    def test_get_collection_empty_name(self, database_manager):
        """Test get_collection with empty name."""
        with pytest.raises(ValueError, match="Collection name cannot be empty"):
            database_manager.get_collection("")

    def test_get_collection_failure(self, database_manager, mock_weaviate_client):
        """Test get_collection failure."""
        mock_weaviate_client.collections.get.side_effect = WeaviateBaseError(
            "Collection not found"
        )

        with pytest.raises(WeaviateBaseError):
            database_manager.get_collection("test_collection")

        # Should have tried with normalized name
        mock_weaviate_client.collections.get.assert_called_once_with("Test_collection")

    def test_create_collection_success(self, database_manager, mock_weaviate_client):
        """Test successful collection creation."""
        mock_collection = Mock()
        mock_weaviate_client.collections.create.return_value = mock_collection

        result = database_manager.create_collection(
            name="test_collection",
            description="Test collection",
            vectorizer_config=None,
            properties=[],
        )

        assert result == mock_collection
        # Name should be normalized in the call
        mock_weaviate_client.collections.create.assert_called_once()
        call_args = mock_weaviate_client.collections.create.call_args
        assert call_args.kwargs["name"] == "Test_collection"

    def test_create_collection_empty_name(self, database_manager):
        """Test create_collection with empty name."""
        with pytest.raises(ValueError, match="Collection name cannot be empty"):
            database_manager.create_collection("")

    def test_create_collection_failure(self, database_manager, mock_weaviate_client):
        """Test create_collection failure."""
        mock_weaviate_client.collections.create.side_effect = WeaviateBaseError(
            "Creation failed"
        )

        with pytest.raises(WeaviateBaseError):
            database_manager.create_collection("test_collection")

    def test_delete_collection_success(self, database_manager, mock_weaviate_client):
        """Test successful collection deletion."""
        result = database_manager.delete_collection("test_collection")

        assert result is True
        # Name should be normalized (first letter capitalized)
        mock_weaviate_client.collections.delete.assert_called_once_with(
            "Test_collection"
        )

    def test_delete_collection_empty_name(self, database_manager):
        """Test delete_collection with empty name."""
        with pytest.raises(ValueError, match="Collection name cannot be empty"):
            database_manager.delete_collection("")

    def test_delete_collection_failure(self, database_manager, mock_weaviate_client):
        """Test delete_collection failure."""
        mock_weaviate_client.collections.delete.side_effect = WeaviateBaseError(
            "Deletion failed"
        )

        with pytest.raises(WeaviateBaseError):
            database_manager.delete_collection("test_collection")

    def test_list_collections_success(self, database_manager, mock_weaviate_client):
        """Test successful collection listing."""
        mock_collections = {"collection1": Mock(), "collection2": Mock()}
        mock_weaviate_client.collections.list_all.return_value = mock_collections

        result = database_manager.list_collections()

        assert result == ["collection1", "collection2"]
        # list_all is called during initialization and during the test
        assert mock_weaviate_client.collections.list_all.call_count >= 1

    def test_list_collections_failure(self, database_manager, mock_weaviate_client):
        """Test list_collections failure."""
        mock_weaviate_client.collections.list_all.side_effect = WeaviateBaseError(
            "List failed"
        )

        with pytest.raises(WeaviateBaseError):
            database_manager.list_collections()

    def test_collection_exists_true(self, database_manager, mock_weaviate_client):
        """Test collection_exists when collection exists."""
        # Collection name in server is capitalized (Weaviate convention)
        mock_collections = {"Test_collection": Mock()}
        mock_weaviate_client.collections.list_all.return_value = mock_collections

        # Input with lowercase first letter should match
        result = database_manager.collection_exists("test_collection")

        assert result is True

    def test_collection_exists_false(self, database_manager, mock_weaviate_client):
        """Test collection_exists when collection does not exist."""
        mock_collections = {"Other_collection": Mock()}
        mock_weaviate_client.collections.list_all.return_value = mock_collections

        result = database_manager.collection_exists("test_collection")

        assert result is False

    def test_collection_exists_empty_name(self, database_manager):
        """Test collection_exists with empty name."""
        with pytest.raises(ValueError, match="Collection name cannot be empty"):
            database_manager.collection_exists("")

    def test_collection_exists_failure(self, database_manager, mock_weaviate_client):
        """Test collection_exists failure."""
        mock_weaviate_client.collections.list_all.side_effect = Exception("List failed")

        result = database_manager.collection_exists("test_collection")

        assert result is False

    def test_get_client(self, database_manager, mock_weaviate_client):
        """Test get_client method."""
        result = database_manager.get_client()
        assert result == mock_weaviate_client

    def test_close(self, database_manager):
        """Test close method."""
        database_manager.close()
        assert database_manager.is_connected is False

    def test_close_no_client(self, database_manager):
        """Test close method when no client exists."""
        delattr(database_manager, "client")
        # Should not raise an exception
        database_manager.close()

    def test_context_manager(self, mock_weaviate_client, mock_connection_params):
        """Test DatabaseManager as context manager."""
        with patch("ragora.core.database_manager.WeaviateClient") as mock_client_class:
            mock_client_class.return_value = mock_weaviate_client

            with DatabaseManager(url="http://localhost:8080") as db_manager:
                assert db_manager.url == "http://localhost:8080"

            # close should be called when exiting context
            assert db_manager.is_connected is False

    def test_normalize_collection_name_basic(self, database_manager):
        """Test _normalize_collection_name with basic lowercase input."""
        result = database_manager._normalize_collection_name("test_collection")
        assert result == "Test_collection"

    def test_normalize_collection_name_capitalized(self, database_manager):
        """Test _normalize_collection_name with capitalized input."""
        result = database_manager._normalize_collection_name("Test_collection")
        assert result == "Test_collection"

    def test_normalize_collection_name_all_lowercase(self, database_manager):
        """Test _normalize_collection_name with all lowercase."""
        result = database_manager._normalize_collection_name("ragora_advanced_usage")
        assert result == "Ragora_advanced_usage"

    def test_normalize_collection_name_preserves_case(self, database_manager):
        """Test _normalize_collection_name preserves case."""
        result = database_manager._normalize_collection_name("test_Advanced_Usage")
        assert result == "Test_Advanced_Usage"

    def test_normalize_collection_name_single_char(self, database_manager):
        """Test _normalize_collection_name with single character."""
        result = database_manager._normalize_collection_name("a")
        assert result == "A"

    def test_normalize_collection_name_empty(self, database_manager):
        """Test _normalize_collection_name with empty string."""
        with pytest.raises(ValueError, match="Collection name cannot be empty"):
            database_manager._normalize_collection_name("")

    def test_normalize_collection_name_whitespace(self, database_manager):
        """Test _normalize_collection_name with whitespace only."""
        with pytest.raises(ValueError, match="Collection name cannot be empty"):
            database_manager._normalize_collection_name("   ")
