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

from weaviate import Client
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
        class_name: str = "Document",
        embedding_engine: Optional[EmbeddingEngine] = None,
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
        self.class_name = class_name
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
            self.client = Client(url, timeout_config=(timeout, timeout))
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

            # Test with a simple query
            self.client.schema.get()
            self.is_connected = True
            return True
        except Exception as e:
            self.is_connected = False
            raise ConnectionError(f"Connection test failed: {str(e)}")

    def create_schema(self, force_recreate: bool = False) -> None:
        """Create the Weaviate schema for document storage.

        Args:
            force_recreate: If True, delete existing schema before creating new one

        Raises:
            WeaviateBaseError: If schema creation fails
        """
        try:
            # Check if schema already exists
            existing_schemas = self.client.schema.get()
            schema_exists = any(
                schema["class"] == self.class_name
                for schema in existing_schemas.get("classes", [])
            )

            if schema_exists:
                if force_recreate:
                    self.logger.info(
                        f"Deleting existing schema for class: {self.class_name}"
                    )
                    self.client.schema.delete_class(self.class_name)
                else:
                    self.logger.info(
                        f"Schema for class {self.class_name} already exists"
                    )
                    return

            # Define the schema
            schema = {
                "class": self.class_name,
                "description": "Document chunks with embeddings for RAG system",
                "vectorizer": "text2vec-transformers",
                "moduleConfig": {
                    "text2vec-transformers": {
                        "model": self.embedding_engine.model_name,
                        "poolingStrategy": "masked_mean",
                        "vectorizeClassName": False,
                    }
                },
                "properties": [
                    {
                        "name": "content",
                        "dataType": ["text"],
                        "description": "The text content of the document chunk",
                        "moduleConfig": {
                            "text2vec-transformers": {
                                "skip": False,
                                "vectorizePropertyName": False,
                            }
                        },
                    },
                    {
                        "name": "chunk_id",
                        "dataType": ["text"],
                        "description": "Unique identifier for the chunk",
                        "moduleConfig": {
                            "text2vec-transformers": {
                                "skip": True,
                                "vectorizePropertyName": False,
                            }
                        },
                    },
                    {
                        "name": "source_document",
                        "dataType": ["text"],
                        "description": "Source document filename",
                        "moduleConfig": {
                            "text2vec-transformers": {
                                "skip": True,
                                "vectorizePropertyName": False,
                            }
                        },
                    },
                    {
                        "name": "chunk_type",
                        "dataType": ["text"],
                        "description": "Type of chunk (text, citation, equation, etc.)",
                        "moduleConfig": {
                            "text2vec-transformers": {
                                "skip": True,
                                "vectorizePropertyName": False,
                            }
                        },
                    },
                    {
                        "name": "metadata_chunk_id",
                        "dataType": ["int"],
                        "description": "Chunk ID from metadata",
                        "moduleConfig": {
                            "text2vec-transformers": {
                                "skip": True,
                                "vectorizePropertyName": False,
                            }
                        },
                    },
                    {
                        "name": "metadata_chunk_size",
                        "dataType": ["int"],
                        "description": "Chunk size from metadata",
                        "moduleConfig": {
                            "text2vec-transformers": {
                                "skip": True,
                                "vectorizePropertyName": False,
                            }
                        },
                    },
                    {
                        "name": "metadata_total_chunks",
                        "dataType": ["int"],
                        "description": "Total chunks from metadata",
                        "moduleConfig": {
                            "text2vec-transformers": {
                                "skip": True,
                                "vectorizePropertyName": False,
                            }
                        },
                    },
                    {
                        "name": "metadata_created_at",
                        "dataType": ["text"],
                        "description": "Created at timestamp from metadata",
                        "moduleConfig": {
                            "text2vec-transformers": {
                                "skip": True,
                                "vectorizePropertyName": False,
                            }
                        },
                    },
                    {
                        "name": "page_number",
                        "dataType": ["int"],
                        "description": "Page number in source document",
                        "moduleConfig": {
                            "text2vec-transformers": {
                                "skip": True,
                                "vectorizePropertyName": False,
                            }
                        },
                    },
                    {
                        "name": "section_title",
                        "dataType": ["text"],
                        "description": "Section or chapter title",
                        "moduleConfig": {
                            "text2vec-transformers": {
                                "skip": True,
                                "vectorizePropertyName": False,
                            }
                        },
                    },
                ],
            }

            # Create the schema
            self.logger.info(f"Creating schema for class: {self.class_name}")
            self.client.schema.create_class(schema)
            self.logger.info(
                f"Successfully created schema for class: {self.class_name}"
            )

        except WeaviateBaseError as e:
            self.logger.error(f"Failed to create schema: {str(e)}")
            raise

    def store_chunk(self, chunk: DataChunk) -> str:
        """Store a single DataChunk in the vector store.

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
            # Prepare the object data
            object_data = {
                "content": chunk.text,
                "chunk_id": chunk.chunk_id,
                "source_document": chunk.source_document,
                "chunk_type": chunk.chunk_type,
                "metadata_chunk_id": chunk.metadata.chunk_id,
                "metadata_chunk_size": chunk.metadata.chunk_size,
                "metadata_total_chunks": chunk.metadata.total_chunks,
                "metadata_created_at": chunk.metadata.created_at or "",
                "page_number": chunk.metadata.page_number or 0,
                "section_title": chunk.metadata.section_title or "",
            }

            # Store the object
            self.logger.debug(f"Storing chunk: {chunk.chunk_id}")
            result = self.client.data_object.create(
                data_object=object_data,
                class_name=self.class_name,
            )

            chunk_uuid = result
            self.logger.debug(
                f"Successfully stored chunk {chunk.chunk_id} with UUID: {chunk_uuid}"
            )
            return chunk_uuid

        except WeaviateBaseError as e:
            self.logger.error(f"Failed to store chunk {chunk.chunk_id}: {str(e)}")
            raise

    def store_chunks(self, chunks: List[DataChunk], batch_size: int = 100) -> List[str]:
        """Store multiple DataChunks in the vector store.

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
            # Ensure schema exists before storing chunks
            self.create_schema()

            self.logger.info(
                f"Storing {total_chunks} chunks in batches of {batch_size}"
            )

            # Process chunks in batches
            for i in range(0, total_chunks, batch_size):
                batch = valid_chunks[i : i + batch_size]
                batch_uuids = []

                # Prepare batch data
                batch_data = []
                for chunk in batch:
                    object_data = {
                        "content": chunk.text,
                        "chunk_id": chunk.chunk_id,
                        "source_document": chunk.source_document,
                        "chunk_type": chunk.chunk_type,
                        "metadata_chunk_id": chunk.metadata.chunk_id,
                        "metadata_chunk_size": chunk.metadata.chunk_size,
                        "metadata_total_chunks": chunk.metadata.total_chunks,
                        "metadata_created_at": chunk.metadata.created_at or "",
                        "page_number": chunk.metadata.page_number or 0,
                        "section_title": chunk.metadata.section_title or "",
                    }
                    batch_data.append(object_data)

                # Store batch
                self.logger.debug(
                    f"Storing batch {i//batch_size + 1} with {len(batch)} chunks"
                )

                # Add objects to batch first
                for obj_data in batch_data:
                    self.client.batch.add_data_object(
                        data_object=obj_data, class_name=self.class_name
                    )

                # Create objects in batch
                batch_result = self.client.batch.create_objects()

                # Extract UUIDs from batch result
                for result in batch_result:
                    if isinstance(result, dict):
                        # Check if the operation was successful
                        if result.get("result", {}).get("status") == "SUCCESS":
                            # Get the ID from the result
                            chunk_id = result.get("id")
                            if chunk_id:
                                batch_uuids.append(chunk_id)
                        else:
                            self.logger.warning(f"Failed to store batch item: {result}")
                    else:
                        self.logger.warning(f"Unexpected result format: {result}")

                stored_uuids.extend(batch_uuids)
                self.logger.debug(
                    f"Stored batch {i//batch_size + 1}, got {len(batch_uuids)} UUIDs"
                )

            self.logger.info(f"Successfully stored {len(stored_uuids)} chunks")
            return stored_uuids

        except WeaviateBaseError as e:
            self.logger.error(f"Failed to store chunks: {str(e)}")
            raise

    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific chunk by its chunk_id.

        Args:
            chunk_id: Unique identifier of the chunk

        Returns:
            Optional[Dict[str, Any]]: Chunk data if found, None otherwise

        Raises:
            WeaviateBaseError: If retrieval operation fails
        """
        try:
            result = (
                self.client.query.get(
                    self.class_name,
                    [
                        "content",
                        "chunk_id",
                        "source_document",
                        "chunk_type",
                        "metadata_chunk_id",
                        "metadata_chunk_size",
                        "metadata_total_chunks",
                        "metadata_created_at",
                        "page_number",
                        "section_title",
                    ],
                )
                .with_where(
                    {
                        "path": ["chunk_id"],
                        "operator": "Equal",
                        "valueString": chunk_id,
                    }
                )
                .with_limit(1)
                .do()
            )

            if result and "data" in result and "Get" in result["data"]:
                chunks = result["data"]["Get"][self.class_name]
                if chunks:
                    return chunks[0]

            return None

        except WeaviateBaseError as e:
            self.logger.error(f"Failed to retrieve chunk {chunk_id}: {str(e)}")
            raise

    def delete_chunk(self, chunk_id: str) -> bool:
        """Delete a chunk by its chunk_id.

        Args:
            chunk_id: Unique identifier of the chunk to delete

        Returns:
            bool: True if deletion was successful, False otherwise

        Raises:
            WeaviateBaseError: If deletion operation fails
        """
        try:
            # First, find the object by chunk_id
            result = (
                self.client.query.get(self.class_name, ["chunk_id"])
                .with_where(
                    {
                        "path": ["chunk_id"],
                        "operator": "Equal",
                        "valueString": chunk_id,
                    }
                )
                .with_additional(["id"])
                .with_limit(1)
                .do()
            )

            if result and "data" in result and "Get" in result["data"]:
                chunks = result["data"]["Get"][self.class_name]
                if chunks:
                    object_id = chunks[0]["_additional"]["id"]
                    self.client.data_object.delete(
                        uuid=object_id, class_name=self.class_name
                    )
                    self.logger.debug(f"Successfully deleted chunk: {chunk_id}")
                    return True

            self.logger.warning(f"Chunk not found for deletion: {chunk_id}")
            return False

        except WeaviateBaseError as e:
            self.logger.error(f"Failed to delete chunk {chunk_id}: {str(e)}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store.

        Returns:
            Dict[str, Any]: Statistics including total objects, class info, etc.

        Raises:
            WeaviateBaseError: If stats retrieval fails
        """
        try:
            # Get total object count
            result = self.client.query.aggregate(self.class_name).with_meta_count().do()

            total_objects = 0
            if result and "data" in result and "Aggregate" in result["data"]:
                aggregate_data = result["data"]["Aggregate"][self.class_name]
                if aggregate_data:
                    total_objects = aggregate_data[0]["meta"]["count"]

            # Get schema information
            schema_info = self.client.schema.get()
            class_info = None
            for schema_class in schema_info.get("classes", []):
                if schema_class["class"] == self.class_name:
                    class_info = schema_class
                    break

            return {
                "total_objects": total_objects,
                "class_name": self.class_name,
                "schema_info": class_info,
                "is_connected": self.is_connected,
                "url": self.url,
            }

        except WeaviateBaseError as e:
            self.logger.error(f"Failed to get stats: {str(e)}")
            raise

    def clear_all(self) -> None:
        """Clear all objects from the vector store.

        Raises:
            WeaviateBaseError: If clearing operation fails
        """
        try:
            self.logger.warning(f"Clearing all objects from class: {self.class_name}")
            self.client.schema.delete_class(self.class_name)
            self.logger.info(
                f"Successfully cleared all objects from class: {self.class_name}"
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
        """Internal method for vector similarity search.

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
            # Build the query
            query_builder = (
                self.client.query.get(
                    self.class_name,
                    [
                        "content",
                        "chunk_id",
                        "source_document",
                        "chunk_type",
                        "metadata_chunk_id",
                        "metadata_chunk_size",
                        "metadata_total_chunks",
                        "metadata_created_at",
                        "page_number",
                        "section_title",
                    ],
                )
                .with_near_text({"concepts": [query]})
                .with_limit(top_k)
                .with_additional(["certainty", "distance"])
            )

            # Apply filters if provided
            if filters:
                where_filter = self._build_where_filter(filters)
                if where_filter:
                    query_builder = query_builder.with_where(where_filter)

            # Execute the query
            self.logger.debug(f"Searching for: '{query}' with top_k={top_k}")
            result = query_builder.do()

            # Process results
            search_results = []
            if result and "data" in result and "Get" in result["data"]:
                for item in result["data"]["Get"][self.class_name]:
                    # Calculate similarity score from certainty
                    certainty = item.get("_additional", {}).get("certainty", 0.0)
                    distance = item.get("_additional", {}).get("distance", 1.0)

                    # Convert certainty to similarity score (0-1 range)
                    similarity_score = certainty if certainty > 0 else 1.0 - distance

                    if similarity_score >= score_threshold:
                        search_results.append(
                            {
                                "content": item.get("content", ""),
                                "chunk_id": item.get("chunk_id", ""),
                                "source_document": item.get("source_document", ""),
                                "chunk_type": item.get("chunk_type", ""),
                                "metadata": {
                                    "chunk_id": item.get("metadata_chunk_id", 0),
                                    "chunk_size": item.get("metadata_chunk_size", 0),
                                    "total_chunks": item.get(
                                        "metadata_total_chunks", 0
                                    ),
                                    "created_at": item.get("metadata_created_at", ""),
                                    "source_document": item.get("source_document", ""),
                                    "page_number": item.get("page_number", 0),
                                    "section_title": item.get("section_title", ""),
                                    "chunk_type": item.get("chunk_type", ""),
                                },
                                "page_number": item.get("page_number", 0),
                                "section_title": item.get("section_title", ""),
                                "similarity_score": similarity_score,
                                "certainty": certainty,
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
        """Internal method for hybrid search.

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
            # Build the hybrid query
            query_builder = (
                self.client.query.get(
                    self.class_name,
                    [
                        "content",
                        "chunk_id",
                        "source_document",
                        "chunk_type",
                        "metadata_chunk_id",
                        "metadata_chunk_size",
                        "metadata_total_chunks",
                        "metadata_created_at",
                        "page_number",
                        "section_title",
                    ],
                )
                .with_hybrid(
                    query=query,
                    alpha=alpha,
                )
                .with_limit(top_k)
                .with_additional(["score"])
            )

            # Apply filters if provided
            if filters:
                where_filter = self._build_where_filter(filters)
                if where_filter:
                    query_builder = query_builder.with_where(where_filter)

            # Execute the query
            self.logger.debug(
                f"Hybrid search for: '{query}' with alpha={alpha}, top_k={top_k}"
            )
            result = query_builder.do()

            # Process results
            search_results = []
            if result and "data" in result and "Get" in result["data"]:
                for item in result["data"]["Get"][self.class_name]:
                    # Get hybrid score
                    hybrid_score = item.get("_additional", {}).get("score", 0.0)

                    if hybrid_score >= score_threshold:
                        search_results.append(
                            {
                                "content": item.get("content", ""),
                                "chunk_id": item.get("chunk_id", ""),
                                "source_document": item.get("source_document", ""),
                                "chunk_type": item.get("chunk_type", ""),
                                "metadata": {
                                    "chunk_id": item.get("metadata_chunk_id", 0),
                                    "chunk_size": item.get("metadata_chunk_size", 0),
                                    "total_chunks": item.get(
                                        "metadata_total_chunks", 0
                                    ),
                                    "created_at": item.get("metadata_created_at", ""),
                                    "source_document": item.get("source_document", ""),
                                    "page_number": item.get("page_number", 0),
                                    "section_title": item.get("section_title", ""),
                                    "chunk_type": item.get("chunk_type", ""),
                                },
                                "page_number": item.get("page_number", 0),
                                "section_title": item.get("section_title", ""),
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

    def _build_where_filter(self, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Build Weaviate where filter from filters dictionary.

        Args:
            filters: Dictionary of filter conditions

        Returns:
            Optional[Dict[str, Any]]: Weaviate where filter or None
        """
        if not filters:
            return None

        # Simple filter building - can be extended for more complex conditions
        where_conditions = []

        for key, value in filters.items():
            if isinstance(value, str):
                where_conditions.append(
                    {"path": [key], "operator": "Equal", "valueString": value}
                )
            elif isinstance(value, int):
                where_conditions.append(
                    {"path": [key], "operator": "Equal", "valueInt": value}
                )
            elif isinstance(value, list):
                where_conditions.append(
                    {
                        "path": [key],
                        "operator": "ContainsAny",
                        "valueStringArray": value,
                    }
                )

        if len(where_conditions) == 1:
            return where_conditions[0]
        elif len(where_conditions) > 1:
            return {"operator": "And", "operands": where_conditions}

        return None
