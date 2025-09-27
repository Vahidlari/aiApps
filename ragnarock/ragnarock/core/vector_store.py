"""Vector store implementation for RAG system using Weaviate.

This module provides the VectorStore class that handles the storage and
retrieval of document embeddings using Weaviate as the vector database.
It focuses solely on storage operations, with search functionality
delegated to the Retriever class.

Key responsibilities:
- Initialize and manage Weaviate client connections
- Store document chunks with embeddings and metadata
- Handle batch operations for efficient indexing
- Provide schema management for different document types
- Integrate with the DataChunk objects from document preprocessing
- Provide internal methods for the Retriever class

The vector store uses Weaviate's built-in text2vec-transformers module for
consistent embedding generation and supports rich metadata filtering.
"""

import logging
from typing import Any, Dict, List, Optional

import weaviate
from weaviate import WeaviateClient
from weaviate.connect import ConnectionParams
from weaviate.exceptions import WeaviateBaseError

from .data_chunker import DataChunk
from .embedding_engine import EmbeddingEngine


class VectorStore:
    """Vector store implementation using Weaviate for document storage.

    This class provides a focused interface for storing and retrieving
    document embeddings using Weaviate as the vector database. It handles
    only storage operations, with search functionality delegated to the
    Retriever class.

    Attributes:
        client: Weaviate client instance
        class_name: Name of the Weaviate class for document storage
        embedding_engine: EmbeddingEngine instance for generating embeddings
        logger: Logger instance for debugging and monitoring
        is_connected: Boolean indicating if connection to Weaviate is active
    """

    def __init__(
        self,
        url: str = "http://localhost:8080",
        grpc_port: int = 50051,
        class_name: str = "Document",
        embedding_engine: Optional[EmbeddingEngine] = None,
        use_client_side_vectorization: bool = False,
        timeout: int = 60,
        retry_attempts: int = 3,
    ):
        """Initialize the VectorStore with Weaviate connection.

        Args:
            url: Weaviate server URL
            class_name: Name of the Weaviate class for document storage
            embedding_engine: EmbeddingEngine instance (optional, will create
                default if not provided)
            timeout: Connection timeout in seconds
            retry_attempts: Number of retry attempts for failed operations

        Raises:
            ConnectionError: If unable to connect to Weaviate
            ValueError: If invalid parameters are provided
        """
        self.url = url
        self.grpc_port = grpc_port
        self.class_name = class_name
        self.use_client_side_vectorization = use_client_side_vectorization
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.is_connected = False

        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Initialize embedding engine if not provided
        if embedding_engine is None:
            self.embedding_engine = EmbeddingEngine()
        else:
            self.embedding_engine = embedding_engine

        # Initialize Weaviate client
        try:
            self.logger.info(f"Connecting to Weaviate at {url}")
            # Parse URL to extract host and port
            connectionParam = ConnectionParams.from_url(
                url=url,
                grpc_port=grpc_port,  # Keep gRPC port but it will fail gracefully
            )
            self.client = WeaviateClient(connectionParam)
            self.client.connect()
            self._test_connection()
            self.logger.info("Successfully connected to Weaviate")

        except Exception as e:
            self.logger.error(f"Failed to connect to Weaviate: {str(e)}")
            raise ConnectionError(f"Could not connect to Weaviate at {url}: {str(e)}")

    def _test_connection(self) -> bool:
        """Test the connection to Weaviate.

        Returns:
            bool: True if connection is successful

        Raises:
            ConnectionError: If connection test fails
        """
        try:
            # Test connection by checking if Weaviate is ready
            if not self.client.is_ready():
                raise ConnectionError("Weaviate is not ready")

            # Test with a simple query - V4 API
            self.client.collections.list_all()
            self.is_connected = True
            return True
        except Exception as e:
            self.is_connected = False
            raise ConnectionError(f"Connection test failed: {str(e)}")

    def create_schema(self, force_recreate: bool = False) -> None:
        """Create the Weaviate collection for document storage using V4 API.

        Args:
            force_recreate: If True, delete existing collection before creating new one

        Raises:
            WeaviateBaseError: If collection creation fails
        """
        try:
            # Check if collection already exists
            existing_collections = self.client.collections.list_all()
            collection_exists = any(
                collection.name == self.class_name
                for collection in existing_collections.values()
            )

            if collection_exists:
                if force_recreate:
                    self.logger.info(f"Deleting existing collection: {self.class_name}")
                    self.client.collections.delete(self.class_name)
                else:
                    self.logger.info(f"Collection {self.class_name} already exists")
                    return

            # Create collection using V4 API
            from weaviate.classes.config import Configure, DataType, Property

            self.logger.info(f"Creating collection: {self.class_name}")

            # Create the collection with V4 API
            self.client.collections.create(
                name=self.class_name,
                description="Document chunks with embeddings for RAG system",
                vectorizer_config=Configure.Vectorizer.text2vec_transformers(),
                properties=[
                    Property(
                        name="content",
                        data_type=DataType.TEXT,
                        description="The text content of the document chunk",
                        vectorize_property_name=False,
                    ),
                    Property(
                        name="chunk_id",
                        data_type=DataType.TEXT,
                        description="Unique identifier for the chunk",
                        vectorize_property_name=False,
                    ),
                    Property(
                        name="source_document",
                        data_type=DataType.TEXT,
                        description="Source document filename",
                        vectorize_property_name=False,
                    ),
                    Property(
                        name="chunk_type",
                        data_type=DataType.TEXT,
                        description="Type of chunk (text, citation, equation, etc.)",
                        vectorize_property_name=False,
                    ),
                    Property(
                        name="metadata_chunk_id",
                        data_type=DataType.INT,
                        description="Chunk ID from metadata",
                        vectorize_property_name=False,
                    ),
                    Property(
                        name="metadata_chunk_size",
                        data_type=DataType.INT,
                        description="Chunk size from metadata",
                        vectorize_property_name=False,
                    ),
                    Property(
                        name="metadata_total_chunks",
                        data_type=DataType.INT,
                        description="Total chunks from metadata",
                        vectorize_property_name=False,
                    ),
                    Property(
                        name="metadata_created_at",
                        data_type=DataType.TEXT,
                        description="Created at timestamp from metadata",
                        vectorize_property_name=False,
                    ),
                    Property(
                        name="page_number",
                        data_type=DataType.INT,
                        description="Page number in source document",
                        vectorize_property_name=False,
                    ),
                    Property(
                        name="section_title",
                        data_type=DataType.TEXT,
                        description="Section or chapter title",
                        vectorize_property_name=False,
                    ),
                ],
            )

            self.logger.info(f"Successfully created collection: {self.class_name}")

        except WeaviateBaseError as e:
            self.logger.error(f"Failed to create collection: {str(e)}")
            raise

    def store_chunk(self, chunk: DataChunk) -> str:
        """Store a single DataChunk in the vector store using V4 API.

        Args:
            chunk: DataChunk object to store

        Returns:
            str: UUID of the stored object

        Raises:
            ValueError: If chunk is invalid
            WeaviateBaseError: If storage operation fails
        """
        if chunk is None:
            raise ValueError("Chunk cannot be None")

        if not chunk.text or not chunk.text.strip():
            raise ValueError("Chunk text cannot be empty")

        try:
            # Ensure collection exists before storing chunks
            self.create_schema()

            # Get the collection
            collection = self.client.collections.get(self.class_name)

            # Prepare the object data
            object_data = self.prepare_data_object(chunk)

            # Store the object using V4 API
            self.logger.debug(f"Storing chunk: {chunk.chunk_id}")
            result = collection.data.insert(object_data)

            chunk_uuid = result
            self.logger.debug(
                f"Successfully stored chunk {chunk.chunk_id} with UUID: {chunk_uuid}"
            )
            return chunk_uuid

        except WeaviateBaseError as e:
            self.logger.error(f"Failed to store chunk {chunk.chunk_id}: {str(e)}")
            raise

    def store_chunks(self, chunks: List[DataChunk], batch_size: int = 100) -> List[str]:
        """Store multiple DataChunks in the vector store using V4 API.

        Args:
            chunks: List of DataChunk objects to store
            batch_size: Number of chunks to process in each batch

        Returns:
            List[str]: List of UUIDs of stored objects

        Raises:
            ValueError: If chunks list is empty or contains invalid chunks
            WeaviateBaseError: If storage operation fails
        """
        if not chunks:
            raise ValueError("Chunks list cannot be empty")

        # Filter out invalid chunks
        valid_chunks = []
        for chunk in chunks:
            if chunk is None or not chunk.text or not chunk.text.strip():
                self.logger.warning(f"Skipping invalid chunk: {chunk}")
                continue
            valid_chunks.append(chunk)

        if not valid_chunks:
            raise ValueError("No valid chunks found in the list")

        stored_uuids = []
        total_chunks = len(valid_chunks)

        try:
            # Ensure collection exists before storing chunks
            self.create_schema()

            # Get the collection
            collection = self.client.collections.get(self.class_name)

            self.logger.info(
                f"Storing {total_chunks} chunks in batches of {batch_size}"
            )

            # Process chunks in batches using V4 API
            for i in range(0, total_chunks, batch_size):
                batch = valid_chunks[i : i + batch_size]

                # Prepare batch data
                batch_data = []
                for chunk in batch:
                    object_data = self.prepare_data_object(chunk)
                    batch_data.append(object_data)

                # Store each chunk individually to avoid gRPC issues
                batch_num = i // batch_size + 1
                self.logger.debug(f"Storing batch {batch_num} with {len(batch)} chunks")

                batch_uuids = []
                for object_data in batch_data:
                    try:
                        # Insert individual object using V4 API
                        result = collection.data.insert(object_data)
                        batch_uuids.append(result)
                    except Exception as e:
                        self.logger.warning(f"Failed to insert object: {e}")
                        continue

                stored_uuids.extend(batch_uuids)
                self.logger.debug(
                    f"Stored batch {batch_num}, got {len(batch_uuids)} UUIDs"
                )

            self.logger.info(f"Successfully stored {len(stored_uuids)} chunks")
            return stored_uuids

        except WeaviateBaseError as e:
            self.logger.error(f"Failed to store chunks: {str(e)}")
            raise

    def prepare_data_object(self, chunk: DataChunk) -> Dict[str, Any]:
        """Prepare the data object for the chunk.

        Args:
            chunk: DataChunk object to prepare

        Returns:
            Dict[str, Any]: Prepared data object
        """
        if chunk is None:
            raise ValueError("Chunk cannot be None")

        if not chunk.text or not chunk.text.strip():
            raise ValueError("Chunk text cannot be empty")

        if not chunk.chunk_id or not chunk.chunk_id.strip():
            raise ValueError("Chunk ID cannot be empty")

        return {
            "content": chunk.text,
            "chunk_id": chunk.chunk_id,
            "source_document": chunk.source_document,
            "chunk_type": chunk.chunk_type,
            "metadata_chunk_id": chunk.metadata.chunk_id,
            "metadata_chunk_size": chunk.metadata.chunk_size,
            "metadata_total_chunks": chunk.metadata.total_chunks,
            "metadata_created_at": (chunk.metadata.created_at or ""),
            "page_number": chunk.metadata.page_number or 0,
            "section_title": chunk.metadata.section_title or "",
        }

    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific chunk by its chunk_id using V4 API.

        Args:
            chunk_id: Unique identifier of the chunk

        Returns:
            Optional[Dict[str, Any]]: Chunk data if found, None otherwise

        Raises:
            WeaviateBaseError: If retrieval operation fails
        """
        try:
            # Get the collection
            collection = self.client.collections.get(self.class_name)

            # Query using V4 API
            from weaviate.classes.query import Filter, MetadataQuery

            result = collection.query.fetch_objects(
                where=Filter.by_property("chunk_id").equal(chunk_id),
                limit=1,
                return_metadata=MetadataQuery(distance=True, score=True),
            )

            if result.objects:
                obj = result.objects[0]
                return {
                    "content": obj.properties.get("content", ""),
                    "chunk_id": obj.properties.get("chunk_id", ""),
                    "source_document": obj.properties.get("source_document", ""),
                    "chunk_type": obj.properties.get("chunk_type", ""),
                    "metadata_chunk_id": obj.properties.get("metadata_chunk_id", 0),
                    "metadata_chunk_size": obj.properties.get("metadata_chunk_size", 0),
                    "metadata_total_chunks": obj.properties.get(
                        "metadata_total_chunks", 0
                    ),
                    "metadata_created_at": obj.properties.get(
                        "metadata_created_at", ""
                    ),
                    "page_number": obj.properties.get("page_number", 0),
                    "section_title": obj.properties.get("section_title", ""),
                }

            return None

        except WeaviateBaseError as e:
            self.logger.error(f"Failed to retrieve chunk {chunk_id}: {str(e)}")
            raise

    def delete_chunk(self, chunk_id: str) -> bool:
        """Delete a chunk by its chunk_id using V4 API.

        Args:
            chunk_id: Unique identifier of the chunk to delete

        Returns:
            bool: True if deletion was successful, False otherwise

        Raises:
            WeaviateBaseError: If deletion operation fails
        """
        try:
            # Get the collection
            collection = self.client.collections.get(self.class_name)

            # First, find the object by chunk_id
            from weaviate.classes.query import Filter

            result = collection.query.fetch_objects(
                where=Filter.by_property("chunk_id").equal(chunk_id), limit=1
            )

            if result.objects:
                obj = result.objects[0]
                # Delete using V4 API
                collection.data.delete_by_id(obj.uuid)
                self.logger.debug(f"Successfully deleted chunk: {chunk_id}")
                return True

            self.logger.warning(f"Chunk not found for deletion: {chunk_id}")
            return False

        except WeaviateBaseError as e:
            self.logger.error(f"Failed to delete chunk {chunk_id}: {str(e)}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store using V4 API.

        Returns:
            Dict[str, Any]: Statistics including total objects, collection info, etc.

        Raises:
            WeaviateBaseError: If stats retrieval fails
        """
        try:
            # Get the collection
            collection = self.client.collections.get(self.class_name)

            # Get total object count using V4 API
            result = collection.aggregate.over_all(total_count=True)

            total_objects = result.total_count if result.total_count is not None else 0

            # Get collection information
            collection_info = {
                "name": collection.name,
                "description": getattr(collection.config, "description", ""),
                "vectorizer": getattr(collection.config, "vectorizer_config", None),
            }

            return {
                "total_objects": total_objects,
                "class_name": self.class_name,
                "collection_info": collection_info,
                "is_connected": self.is_connected,
                "url": self.url,
            }

        except WeaviateBaseError as e:
            self.logger.error(f"Failed to get stats: {str(e)}")
            raise

    def clear_all(self) -> None:
        """Clear all objects from the vector store using V4 API.

        Raises:
            WeaviateBaseError: If clearing operation fails
        """
        try:
            self.logger.warning(
                f"Clearing all objects from collection: {self.class_name}"
            )
            self.client.collections.delete(self.class_name)
            self.logger.info(
                f"Successfully cleared all objects from collection: "
                f"{self.class_name}"
            )
        except WeaviateBaseError as e:
            self.logger.error(f"Failed to clear all objects: {str(e)}")
            raise

    def close(self) -> None:
        """Close the connection to Weaviate."""
        try:
            if hasattr(self, "client") and self.client:
                # Weaviate client doesn't have an explicit close method
                # but we can mark the connection as closed
                self.is_connected = False
                self.logger.info("Vector store connection closed")
        except Exception as e:
            self.logger.error(f"Error closing vector store: {str(e)}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    # Internal methods for Retriever class
    def _search_similar_internal(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Internal method for vector similarity search using V4 API.

        This method is used by the Retriever class and should not be called
        directly by users. Use the Retriever class for search operations.

        Args:
            query: Search query text
            top_k: Number of results to return
            score_threshold: Minimum similarity score threshold
            filters: Optional filters to apply to the search

        Returns:
            List[Dict[str, Any]]: List of search results with metadata

        Raises:
            ValueError: If query is empty
            WeaviateBaseError: If search operation fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            # Get the collection
            collection = self.client.collections.get(self.class_name)

            # Build the query using V4 API
            from weaviate.classes.query import MetadataQuery

            # Apply filters if provided
            where_filter = None
            if filters:
                where_filter = self._build_where_filter_v4(filters)

            # Execute the query using REST API (since gRPC is not available)
            self.logger.debug(f"Searching for: '{query}' with top_k={top_k}")
            result = self._search_via_rest_api(query, top_k, where_filter)

            # Process results
            search_results = []
            for obj in result:
                # Calculate similarity score from distance
                distance = obj.get("_additional", {}).get("distance", 1.0)
                similarity_score = 1.0 - distance

                if similarity_score >= score_threshold:
                    search_results.append(
                        {
                            "content": obj.get("content", ""),
                            "chunk_id": obj.get("chunk_id", ""),
                            "source_document": obj.get("source_document", ""),
                            "chunk_type": obj.get("chunk_type", ""),
                            "metadata": {
                                "chunk_id": obj.get("metadata_chunk_id", 0),
                                "chunk_size": obj.get("metadata_chunk_size", 0),
                                "total_chunks": obj.get("metadata_total_chunks", 0),
                                "created_at": obj.get("metadata_created_at", ""),
                                "source_document": obj.get("source_document", ""),
                                "page_number": obj.get("page_number", 0),
                                "section_title": obj.get("section_title", ""),
                                "chunk_type": obj.get("chunk_type", ""),
                            },
                            "page_number": obj.get("page_number", 0),
                            "section_title": obj.get("section_title", ""),
                            "similarity_score": similarity_score,
                            "distance": distance,
                        }
                    )

            self.logger.debug(
                f"Found {len(search_results)} results for query: '{query}'"
            )
            return search_results

        except WeaviateBaseError as e:
            self.logger.error(f"Failed to search similar documents: {str(e)}")
            raise

    def _search_hybrid_internal(
        self,
        query: str,
        top_k: int = 5,
        alpha: float = 0.5,
        score_threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Internal method for hybrid search using V4 API.

        This method is used by the Retriever class and should not be called
        directly by users. Use the Retriever class for search operations.

        Args:
            query: Search query text
            top_k: Number of results to return
            alpha: Weight for vector search (0.0 = keyword only, 1.0 = vector only)
            score_threshold: Minimum similarity score threshold
            filters: Optional filters to apply to the search

        Returns:
            List[Dict[str, Any]]: List of search results with metadata

        Raises:
            ValueError: If query is empty or alpha is out of range
            WeaviateBaseError: If search operation fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if not 0.0 <= alpha <= 1.0:
            raise ValueError("Alpha must be between 0.0 and 1.0")

        try:
            # Get the collection
            collection = self.client.collections.get(self.class_name)

            # Build the hybrid query using V4 API
            from weaviate.classes.query import MetadataQuery

            # Apply filters if provided
            where_filter = None
            if filters:
                where_filter = self._build_where_filter_v4(filters)

            # Execute the hybrid query using REST API (since gRPC is not available)
            self.logger.debug(
                f"Hybrid search for: '{query}' with alpha={alpha}, " f"top_k={top_k}"
            )
            result = self._search_hybrid_via_rest_api(query, top_k, alpha, where_filter)

            # Process results
            search_results = []
            for obj in result:
                # Get hybrid score
                hybrid_score = obj.get("_additional", {}).get("score", 0.0)

                if hybrid_score >= score_threshold:
                    search_results.append(
                        {
                            "content": obj.get("content", ""),
                            "chunk_id": obj.get("chunk_id", ""),
                            "source_document": obj.get("source_document", ""),
                            "chunk_type": obj.get("chunk_type", ""),
                            "metadata": {
                                "chunk_id": obj.get("metadata_chunk_id", 0),
                                "chunk_size": obj.get("metadata_chunk_size", 0),
                                "total_chunks": obj.get("metadata_total_chunks", 0),
                                "created_at": obj.get("metadata_created_at", ""),
                                "source_document": obj.get("source_document", ""),
                                "page_number": obj.get("page_number", 0),
                                "section_title": obj.get("section_title", ""),
                                "chunk_type": obj.get("chunk_type", ""),
                            },
                            "page_number": obj.get("page_number", 0),
                            "section_title": obj.get("section_title", ""),
                            "similarity_score": hybrid_score,
                            "hybrid_score": hybrid_score,
                        }
                    )

            self.logger.debug(
                f"Found {len(search_results)} results for hybrid query: '{query}'"
            )
            return search_results

        except WeaviateBaseError as e:
            self.logger.error(f"Failed to perform hybrid search: {str(e)}")
            raise

    def _build_where_filter_v4(self, filters: Dict[str, Any]):
        """Build Weaviate V4 where filter from filters dictionary.

        Args:
            filters: Dictionary of filter conditions

        Returns:
            Filter object or None
        """
        if not filters:
            return None

        from weaviate.classes.query import Filter

        # Simple filter building for V4 API
        conditions = []

        for key, value in filters.items():
            if isinstance(value, str):
                conditions.append(Filter.by_property(key).equal(value))
            elif isinstance(value, int):
                conditions.append(Filter.by_property(key).equal(value))
            elif isinstance(value, list):
                conditions.append(Filter.by_property(key).contains_any(value))

        if len(conditions) == 1:
            return conditions[0]
        elif len(conditions) > 1:
            return Filter.and_(*conditions)

        return None

    def _search_via_rest_api(self, query: str, top_k: int, where_filter=None):
        """Search using REST API directly to avoid gRPC issues.

        Args:
            query: Search query text
            top_k: Number of results to return
            where_filter: Optional filter conditions

        Returns:
            List of search results
        """
        import json

        import requests

        url = f"{self.url}/v1/graphql"

        # Build the GraphQL query
        graphql_query = f"""
        {{
            Get {{
                {self.class_name}(
                    nearText: {{
                        concepts: ["{query}"]
                    }}
                    limit: {top_k}
                ) {{
                    content
                    chunk_id
                    source_document
                    chunk_type
                    metadata_chunk_id
                    metadata_chunk_size
                    metadata_total_chunks
                    metadata_created_at
                    page_number
                    section_title
                    _additional {{
                        distance
                    }}
                }}
            }}
        }}
        """

        payload = {"query": graphql_query}

        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                objects = data.get("data", {}).get("Get", {}).get(self.class_name, [])
                return objects
            else:
                self.logger.error(
                    f"REST API error: {response.status_code} - {response.text}"
                )
                return []
        except Exception as e:
            self.logger.error(f"REST API request failed: {e}")
            return []

    def _search_hybrid_via_rest_api(
        self, query: str, top_k: int, alpha: float = 0.5, where_filter=None
    ):
        """Hybrid search using REST API directly to avoid gRPC issues.

        Args:
            query: Search query text
            top_k: Number of results to return
            alpha: Balance between vector and keyword search (0.0 = pure keyword, 1.0 = pure vector)
            where_filter: Optional filter conditions

        Returns:
            List of search results
        """
        import json

        import requests

        url = f"{self.url}/v1/graphql"

        # Build the GraphQL query for hybrid search
        graphql_query = f"""
        {{
            Get {{
                {self.class_name}(
                    hybrid: {{
                        query: "{query}"
                        alpha: {alpha}
                    }}
                    limit: {top_k}
                ) {{
                    content
                    chunk_id
                    source_document
                    chunk_type
                    metadata_chunk_id
                    metadata_chunk_size
                    metadata_total_chunks
                    metadata_created_at
                    page_number
                    section_title
                    _additional {{
                        score
                    }}
                }}
            }}
        }}
        """

        payload = {"query": graphql_query}

        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                objects = data.get("data", {}).get("Get", {}).get(self.class_name, [])
                return objects
            else:
                self.logger.error(
                    f"REST API error: {response.status_code} - {response.text}"
                )
                return []
        except Exception as e:
            self.logger.error(f"REST API request failed: {e}")
            return []
