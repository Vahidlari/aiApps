"""Integration tests for DatabaseManager, Retriever, and VectorStore.

This module contains integration tests that verify the DatabaseManager,
Retriever, and VectorStore components work together correctly in the
three-layer architecture design.
"""

from unittest.mock import Mock, patch

import pytest

from ragora.core.chunking import ChunkMetadata, DataChunk
from ragora.core.database_manager import DatabaseManager
from ragora.core.retriever import Retriever
from ragora.core.vector_store import VectorStore


class TestDatabaseManagerRetrieverVectorStoreIntegration:
    """Integration tests for DatabaseManager, Retriever, and VectorStore."""

    @pytest.fixture
    def mock_weaviate_client(self):
        """Create a mock Weaviate client for integration testing."""
        client = Mock()
        client.is_ready.return_value = True
        client.collections.list_all.return_value = {}
        return client

    @pytest.fixture
    def mock_collection(self):
        """Create a mock Weaviate collection."""
        collection = Mock()
        return collection

    @pytest.fixture
    def sample_chunk(self):
        """Create a sample DataChunk for integration testing."""
        metadata = ChunkMetadata(
            chunk_idx=1,
            chunk_size=100,
            total_chunks=5,
            created_at="2023-01-01T00:00:00",
            page_number=1,
            section_title="Machine Learning",
        )
        return DataChunk(
            text="This is a test document about machine learning algorithms "
            "and neural networks.",
            start_idx=0,
            end_idx=89,
            metadata=metadata,
            chunk_id="test_chunk_1",
            source_document="ml_document.pdf",
            chunk_type="text",
        )

    @pytest.fixture
    def mock_search_result(self):
        """Create a mock search result for integration testing."""
        obj = Mock()
        obj.properties = {
            "content": "This is a test document about machine learning algorithms "
            "and neural networks.",
            "chunk_id": "test_chunk_1",
            "source_document": "ml_document.pdf",
            "chunk_type": "text",
            "metadata_chunk_idx": 1,
            "metadata_chunk_size": 100,
            "metadata_total_chunks": 5,
            "metadata_created_at": "2023-01-01T00:00:00",
            "page_number": 1,
            "section_title": "Machine Learning",
        }
        obj.metadata = Mock()
        obj.metadata.distance = 0.2
        obj.metadata.score = 0.8
        return obj

    def test_database_manager_vector_store_integration(
        self, mock_weaviate_client, mock_collection, sample_chunk
    ):
        """Test integration between DatabaseManager and VectorStore."""
        with patch("ragora.core.database_manager.ConnectionParams"):
            with patch(
                "ragora.core.database_manager.WeaviateClient"
            ) as mock_client_class:
                with patch("ragora.core.vector_store.generate_uuid5") as mock_uuid:
                    mock_client_class.return_value = mock_weaviate_client
                    mock_uuid.return_value = "test_uuid"

                    # Create DatabaseManager
                    db_manager = DatabaseManager(url="http://localhost:8080")
                    db_manager.client = mock_weaviate_client

                    # Create VectorStore with DatabaseManager
                    vector_store = VectorStore(
                        db_manager=db_manager, collection="TestDocument"
                    )

                    # Test schema creation
                    mock_weaviate_client.collections.list_all.return_value = {}
                    mock_weaviate_client.collections.create.return_value = (
                        mock_collection
                    )

                    vector_store.create_schema("TestDocument")

                    # Verify DatabaseManager methods were called
                    mock_weaviate_client.collections.create.assert_called_once()

                    # Test chunk storage
                    mock_weaviate_client.collections.get.return_value = mock_collection
                    mock_collection.data.insert.return_value = "test_uuid"

                    result = vector_store.store_chunk(sample_chunk, "TestDocument")

                    assert result == "test_uuid"
                    mock_weaviate_client.collections.get.assert_called_with(
                        "TestDocument"
                    )

    def test_database_manager_retriever_integration(
        self, mock_weaviate_client, mock_collection, mock_search_result
    ):
        """Test integration between DatabaseManager and Retriever."""
        with patch("ragora.core.database_manager.ConnectionParams"):
            with patch(
                "ragora.core.database_manager.WeaviateClient"
            ) as mock_client_class:
                mock_client_class.return_value = mock_weaviate_client

                # Create DatabaseManager
                db_manager = DatabaseManager(url="http://localhost:8080")
                db_manager.client = mock_weaviate_client

                # Create Retriever with DatabaseManager
                retriever = Retriever(db_manager=db_manager)

                # Test vector search
                mock_result = Mock()
                mock_result.objects = [mock_search_result]
                mock_collection.query.near_text.return_value = mock_result
                mock_weaviate_client.collections.get.return_value = mock_collection

                with patch.object(
                    retriever, "_preprocess_query", return_value="machine learning"
                ):
                    with patch.object(
                        retriever, "_process_vector_results"
                    ) as mock_process:
                        mock_process.return_value = [
                            {"content": "test", "similarity_score": 0.8}
                        ]

                        results = retriever.search_similar(
                            "machine learning", collection="TestDocument"
                        )

                        assert len(results) == 1
                        mock_weaviate_client.collections.get.assert_called_with(
                            "TestDocument"
                        )

    def test_full_workflow_integration(
        self, mock_weaviate_client, mock_collection, sample_chunk, mock_search_result
    ):
        """Test complete workflow: DatabaseManager -> VectorStore -> Retriever."""
        with patch("ragora.core.database_manager.ConnectionParams"):
            with patch(
                "ragora.core.database_manager.WeaviateClient"
            ) as mock_client_class:
                with patch("ragora.core.vector_store.generate_uuid5") as mock_uuid:
                    mock_client_class.return_value = mock_weaviate_client
                    mock_uuid.return_value = "test_uuid"

                    # Create DatabaseManager
                    db_manager = DatabaseManager(url="http://localhost:8080")
                    db_manager.client = mock_weaviate_client

                    # Create VectorStore and Retriever with same DatabaseManager
                    vector_store = VectorStore(
                        db_manager=db_manager, collection="TestDocument"
                    )

                    retriever = Retriever(db_manager=db_manager)

                    # Test complete workflow

                    # 1. Create schema
                    mock_weaviate_client.collections.list_all.return_value = {}
                    mock_weaviate_client.collections.create.return_value = (
                        mock_collection
                    )
                    vector_store.create_schema("TestDocument")

                    # 2. Store document
                    mock_weaviate_client.collections.get.return_value = mock_collection
                    mock_collection.data.insert.return_value = "test_uuid"
                    uuid = vector_store.store_chunk(sample_chunk, "TestDocument")
                    assert uuid == "test_uuid"

                    # 3. Search for document
                    mock_result = Mock()
                    mock_result.objects = [mock_search_result]
                    mock_collection.query.near_text.return_value = mock_result

                    with patch.object(
                        retriever, "_preprocess_query", return_value="machine learning"
                    ):
                        with patch.object(
                            retriever, "_process_vector_results"
                        ) as mock_process:
                            mock_process.return_value = [
                                {"content": "test", "similarity_score": 0.8}
                            ]

                            results = retriever.search_similar(
                                "machine learning", collection="TestDocument"
                            )

                            assert len(results) == 1
                            assert results[0]["similarity_score"] == 0.8

    def test_multiple_search_methods_integration(
        self, mock_weaviate_client, mock_collection, mock_search_result
    ):
        """Test that Retriever can perform all search methods with DatabaseManager."""
        with patch("ragora.core.database_manager.ConnectionParams"):
            with patch(
                "ragora.core.database_manager.WeaviateClient"
            ) as mock_client_class:
                mock_client_class.return_value = mock_weaviate_client

                # Create DatabaseManager and Retriever
                db_manager = DatabaseManager(url="http://localhost:8080")
                db_manager.client = mock_weaviate_client

                retriever = Retriever(db_manager=db_manager)

                mock_result = Mock()
                mock_result.objects = [mock_search_result]
                mock_weaviate_client.collections.get.return_value = mock_collection

                with patch.object(
                    retriever, "_preprocess_query", return_value="machine learning"
                ):
                    # Test vector search
                    mock_collection.query.near_text.return_value = mock_result
                    with patch.object(
                        retriever, "_process_vector_results"
                    ) as mock_process:
                        mock_process.return_value = [{"similarity_score": 0.8}]
                        vector_results = retriever.search_similar(
                            "machine learning", collection="TestDocument"
                        )
                        assert len(vector_results) == 1

                    # Test hybrid search
                    mock_collection.query.hybrid.return_value = mock_result
                    with patch.object(
                        retriever, "_process_hybrid_results"
                    ) as mock_process:
                        mock_process.return_value = [{"hybrid_score": 0.8}]
                        hybrid_results = retriever.search_hybrid(
                            "machine learning", collection="TestDocument", alpha=0.5
                        )
                        assert len(hybrid_results) == 1

                    # Test keyword search
                    mock_collection.query.bm25.return_value = mock_result
                    with patch.object(
                        retriever, "_process_keyword_results"
                    ) as mock_process:
                        mock_process.return_value = [{"bm25_score": 0.8}]
                        keyword_results = retriever.search_keyword(
                            "machine learning", collection="TestDocument"
                        )
                        assert len(keyword_results) == 1

    def test_error_handling_integration(self, mock_weaviate_client):
        """Test error handling across components."""
        with patch("ragora.core.database_manager.ConnectionParams"):
            with patch(
                "ragora.core.database_manager.WeaviateClient"
            ) as mock_client_class:
                mock_client_class.return_value = mock_weaviate_client

                # Test DatabaseManager connection failure
                mock_weaviate_client.connect.side_effect = Exception(
                    "Connection failed"
                )

                with pytest.raises(ConnectionError):
                    DatabaseManager(url="http://localhost:8080")

                # Reset mock
                mock_weaviate_client.connect.side_effect = None
                mock_weaviate_client.is_ready.return_value = True

                # Test VectorStore with None DatabaseManager
                with pytest.raises(ValueError, match="DatabaseManager cannot be None"):
                    VectorStore(db_manager=None)

                # Test Retriever with None DatabaseManager
                with pytest.raises(ValueError, match="DatabaseManager cannot be None"):
                    Retriever(db_manager=None)

    def test_context_managers_integration(self, mock_weaviate_client, mock_collection):
        """Test context manager functionality across components."""
        with patch("ragora.core.database_manager.ConnectionParams"):
            with patch(
                "ragora.core.database_manager.WeaviateClient"
            ) as mock_client_class:
                mock_client_class.return_value = mock_weaviate_client

                # Test DatabaseManager context manager
                with DatabaseManager(url="http://localhost:8080") as db_manager:
                    assert db_manager.url == "http://localhost:8080"
                    assert db_manager.is_connected is True

                # Test VectorStore context manager
                with VectorStore(
                    db_manager=db_manager, collection="TestDocument"
                ) as vector_store:
                    assert vector_store.collection == "TestDocument"

                # Verify close methods were called
                assert db_manager.is_connected is False

    def test_statistics_integration(self, mock_weaviate_client, mock_collection):
        """Test statistics collection across components."""
        with patch("ragora.core.database_manager.ConnectionParams"):
            with patch(
                "ragora.core.database_manager.WeaviateClient"
            ) as mock_client_class:
                mock_client_class.return_value = mock_weaviate_client

                db_manager = DatabaseManager(url="http://localhost:8080")
                db_manager.client = mock_weaviate_client

                # Test VectorStore stats
                vector_store = VectorStore(
                    db_manager=db_manager, collection="TestDocument"
                )
                mock_weaviate_client.collections.get.return_value = mock_collection

                mock_agg_result = Mock()
                mock_agg_result.total_count = 100
                mock_collection.aggregate.over_all.return_value = mock_agg_result
                mock_collection.name = "TestDocument"
                mock_collection.config = Mock()
                mock_collection.config.description = "Test collection"
                mock_collection.config.vectorizer_config = None

                vector_stats = vector_store.get_stats("TestDocument")
                assert vector_stats["total_objects"] == 100
                assert vector_stats["collection"] == mock_collection

                # Test Retriever stats
                retriever = Retriever(db_manager=db_manager)
                mock_weaviate_client.collections.list_all.return_value = {
                    "TestDocument": Mock()
                }

                retriever_stats = retriever.get_retrieval_stats(
                    collection="TestDocument"
                )
                assert "database_stats" in retriever_stats
                assert "retrieval_methods" in retriever_stats
                assert "vector_similarity" in retriever_stats["retrieval_methods"]
                assert "hybrid_search" in retriever_stats["retrieval_methods"]
                assert "keyword_search" in retriever_stats["retrieval_methods"]
