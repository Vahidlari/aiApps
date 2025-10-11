"""Vector store implementation for RAG system using Weaviate.

This module provides the VectorStore class that handles the storage and
retrieval of document embeddings using Weaviate as the vector database.
It focuses solely on storage operations, with search functionality
delegated to the Retriever class.

Key responsibilities:
- Store document chunks with embeddings and metadata
- Handle batch operations for efficient indexing
- Provide schema management for different document types
- Integrate with the DataChunk objects from document preprocessing
- Use DatabaseManager for low-level database operations

The vector store uses Weaviate's built-in text2vec-transformers module for
consistent embedding generation and supports rich metadata filtering.
"""

import logging
from typing import Any, Dict, List, Optional

from weaviate.classes.config import Configure, DataType, Property
from weaviate.classes.query import Filter, MetadataQuery
from weaviate.exceptions import WeaviateBaseError

from .data_chunker import DataChunk
from .database_manager import DatabaseManager
from .embedding_engine import EmbeddingEngine


class VectorStore:
    """Vector store implementation using Weaviate for document storage.

    This class provides a focused interface for storing and retrieving
    document embeddings using Weaviate as the vector database. It handles
    only storage operations, with search functionality delegated to the
    Retriever class.

    Attributes:
        db_manager: DatabaseManager instance for database operations
        class_name: Name of the Weaviate class for document storage
        embedding_engine: EmbeddingEngine instance for generating embeddings
        logger: Logger instance for debugging and monitoring
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        class_name: str = "Document",
        embedding_engine: Optional[EmbeddingEngine] = None,
    ):
        """Initialize the VectorStore with DatabaseManager.

        Args:
            db_manager: DatabaseManager instance for database operations
            class_name: Name of the Weaviate class for document storage
            embedding_engine: EmbeddingEngine instance (optional, will create
                default if not provided)

        Raises:
            ValueError: If invalid parameters are provided
        """
        if db_manager is None:
            raise ValueError("DatabaseManager cannot be None")

        self.db_manager = db_manager
        self.class_name = class_name

        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Initialize embedding engine if not provided
        if embedding_engine is None:
            self.embedding_engine = EmbeddingEngine()
        else:
            self.embedding_engine = embedding_engine

    def is_connected(self) -> bool:
        """Check if the vector store is connected to the database.

        Returns:
            bool: True if connected
        """
        return self.db_manager.is_connected

    def create_schema(self, class_name: str, force_recreate: bool = False) -> None:
        """Create the Weaviate collection for document storage using V4 API.

        Args:
            force_recreate: If True, delete existing collection before creating new one

        Raises:
            WeaviateBaseError: If collection creation fails
        """
        try:
            # Check if collection already exists
            collection_exists = self.db_manager.collection_exists(class_name)

            if collection_exists:
                if force_recreate:
                    self.logger.info(f"Deleting existing collection: {class_name}")
                    self.db_manager.delete_collection(class_name)
                else:
                    self.logger.info(f"Collection {class_name} already exists")
                    return

            # Define schema properties
            properties = [
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
            ]

            self.logger.info(f"Creating collection: {class_name}")

            # Create the collection using DatabaseManager
            self.db_manager.create_collection(
                name=class_name,
                description="Document chunks with embeddings for RAG system",
                vectorizer_config=Configure.Vectorizer.text2vec_transformers(),
                properties=properties,
            )

            self.logger.info(f"Successfully created collection: {class_name}")

        except WeaviateBaseError as e:
            self.logger.error(f"Failed to create collection: {str(e)}")
            raise

    def store_chunk(self, chunk: DataChunk, class_name: str) -> str:
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
            self.create_schema(class_name)

            # Get the collection
            collection = self.db_manager.get_collection(self.class_name)

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

    def store_chunks(
        self, chunks: List[DataChunk], class_name: str, batch_size: int = 100
    ) -> List[str]:
        """Store multiple DataChunks in the vector store using V4 API.

        Args:
            chunks: List of DataChunk objects to store
            class_name: Name of the Weaviate class for document storage
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
            self.create_schema(class_name)

            # Get the collection
            collection = self.db_manager.get_collection(class_name)

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

    def get_chunk_by_id(
        self, chunk_id: str, class_name: str
    ) -> Optional[Dict[str, Any]]:
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
            collection = self.db_manager.get_collection(class_name)

            # Query using V4 API
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

    def delete_chunk(self, chunk_id: str, class_name: str) -> bool:
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
            collection = self.db_manager.get_collection(class_name)

            # First, find the object by chunk_id
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

    def get_stats(self, class_name: str) -> Dict[str, Any]:
        """Get statistics about the vector store using V4 API.

        Returns:
            Dict[str, Any]: Statistics including total objects, collection info, etc.

        Raises:
            WeaviateBaseError: If stats retrieval fails
        """
        try:
            # Get the collection
            collection = self.db_manager.get_collection(class_name)

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
                "class_name": class_name,
                "collection_info": collection_info,
                "is_connected": self.is_connected(),
                "db_manager_url": self.db_manager.url,
            }

        except WeaviateBaseError as e:
            self.logger.error(f"Failed to get stats: {str(e)}")
            raise

    def clear_all(self, class_name: str) -> None:
        """Clear all objects from the vector store using V4 API.

        Raises:
            WeaviateBaseError: If clearing operation fails
        """
        try:
            self.logger.warning(f"Clearing all objects from collection: {class_name}")
            self.db_manager.delete_collection(class_name)
            self.logger.info(
                f"Successfully cleared all objects from collection: " f"{class_name}"
            )
        except WeaviateBaseError as e:
            self.logger.error(f"Failed to clear all objects: {str(e)}")
            raise

    def close(self) -> None:
        """Close the connection to Weaviate."""
        try:
            if hasattr(self, "db_manager") and self.db_manager:
                self.db_manager.close()
                self.logger.info("Vector store connection closed")
        except Exception as e:
            self.logger.error(f"Error closing vector store: {str(e)}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
