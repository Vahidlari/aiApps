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

import json
import logging
from typing import Any, Dict, List, Optional

from weaviate.classes.config import Configure, DataType, Property
from weaviate.exceptions import WeaviateBaseError
from weaviate.util import generate_uuid5

from .chunking import DataChunk
from .database_manager import DatabaseManager
from .embedding_engine import EmbeddingEngine
from .models import RetrievalMetadata, RetrievalResultItem


class VectorStore:
    """Vector store implementation using Weaviate for document storage.

    This class provides a focused interface for storing and retrieving
    document embeddings using Weaviate as the vector database. It handles
    only storage operations, with search functionality delegated to the
    Retriever class.

    Attributes:
        db_manager: DatabaseManager instance for database operations
        collection: Name of the Weaviate class for document storage
        embedding_engine: EmbeddingEngine instance for generating embeddings
        logger: Logger instance for debugging and monitoring
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        collection: str = "Document",
        embedding_engine: Optional[EmbeddingEngine] = None,
    ):
        """Initialize the VectorStore with DatabaseManager.

        Args:
            db_manager: DatabaseManager instance for database operations
            collection: Name of the Weaviate class for document storage
            embedding_engine: EmbeddingEngine instance (optional, defaults to None)

        Raises:
            ValueError: If invalid parameters are provided
        """
        if db_manager is None:
            raise ValueError("DatabaseManager cannot be None")

        self.db_manager = db_manager
        self.collection = collection

        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Note: Embedding engine is not needed when using Weaviate's text2vec-transformers
        # Weaviate handles embeddings server-side. EmbeddingEngine is only kept for
        # potential future use cases where client-side embeddings might be needed.
        # DO NOT initialize it by default to avoid unnecessary model loading.
        self.embedding_engine = embedding_engine

    def is_connected(self) -> bool:
        """Check if the vector store is connected to the database.

        Returns:
            bool: True if connected
        """
        return self.db_manager.is_connected

    def create_schema(self, collection: str, force_recreate: bool = False) -> None:
        """Create the Weaviate collection for document storage using V4 API.

        Args:
            collection: Name of the collection for document storage
            force_recreate: If True, delete existing collection before
                creating new one

        Returns:
            None

        Raises:
            WeaviateBaseError: If collection creation fails
        """
        try:
            # Check if collection already exists
            collection_exists = self.db_manager.collection_exists(collection)

            if collection_exists:
                if force_recreate:
                    self.logger.info(f"Deleting existing collection: {collection}")
                    self.db_manager.delete_collection(collection)
                else:
                    self.logger.info(
                        f"Collection {collection} already exists returning without creating new one"
                    )
                    return
            else:
                self.logger.info(f"Creating new collection: {collection}")
            # Define schema properties
            properties = [
                # Core fields
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
                    name="chunk_key",
                    data_type=DataType.TEXT,
                    description="Key for the chunk (UUID5)",
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
                    name="created_at",
                    data_type=DataType.TEXT,
                    description="Creation timestamp",
                    vectorize_property_name=False,
                ),
                # Document-specific fields
                Property(
                    name="metadata_chunk_idx",
                    data_type=DataType.INT,
                    description="Chunk index from metadata",
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
                # Email-specific fields
                Property(
                    name="email_subject",
                    data_type=DataType.TEXT,
                    description="Email subject line",
                    vectorize_property_name=False,
                ),
                Property(
                    name="email_sender",
                    data_type=DataType.TEXT,
                    description="Email sender address",
                    vectorize_property_name=False,
                ),
                Property(
                    name="email_recipient",
                    data_type=DataType.TEXT,
                    description="Email recipient address",
                    vectorize_property_name=False,
                ),
                Property(
                    name="email_date",
                    data_type=DataType.TEXT,
                    description="Email timestamp",
                    vectorize_property_name=False,
                ),
                Property(
                    name="email_id",
                    data_type=DataType.TEXT,
                    description="Unique email identifier",
                    vectorize_property_name=False,
                ),
                Property(
                    name="email_folder",
                    data_type=DataType.TEXT,
                    description="Email folder/path",
                    vectorize_property_name=False,
                ),
                # Custom metadata fields
                Property(
                    name="custom_metadata",
                    data_type=DataType.TEXT,
                    description="Custom metadata as JSON string",
                    vectorize_property_name=False,
                ),
                Property(
                    name="language",
                    data_type=DataType.TEXT,
                    description="Content language (e.g., en, es, fr)",
                    vectorize_property_name=False,
                ),
                Property(
                    name="domain",
                    data_type=DataType.TEXT,
                    description="Content domain (e.g., scientific, legal, medical)",
                    vectorize_property_name=False,
                ),
                Property(
                    name="confidence",
                    data_type=DataType.NUMBER,
                    description="Processing confidence score (0.0-1.0)",
                    vectorize_property_name=False,
                ),
                Property(
                    name="tags",
                    data_type=DataType.TEXT,
                    description="Comma-separated tags/categories",
                    vectorize_property_name=False,
                ),
                Property(
                    name="priority",
                    data_type=DataType.INT,
                    description="Content priority/importance level",
                    vectorize_property_name=False,
                ),
                Property(
                    name="content_category",
                    data_type=DataType.TEXT,
                    description="Fine-grained content categorization",
                    vectorize_property_name=False,
                ),
            ]

            self.logger.info(f"Creating collection: {collection}")

            # Create the collection using DatabaseManager
            self.db_manager.create_collection(
                name=collection,
                description="Document chunks with embeddings for RAG system",
                vectorizer_config=Configure.Vectorizer.text2vec_transformers(),
                properties=properties,
            )

            self.logger.info(f"Successfully created collection: {collection}")

        except WeaviateBaseError as e:
            self.logger.error(f"Failed to create collection: {str(e)}")
            raise

    def store_chunk(self, chunk: DataChunk, collection: str) -> str:
        """Store a single DataChunk in the vector store using V4 API.

        Args:
            chunk: DataChunk object to store
            collection: Name of the Weaviate class for document storage
        Returns:
            str: UUID of the stored chunk

        Raises:
            ValueError: If chunk is None or empty
            WeaviateBaseError: If storage operation fails
        """
        if chunk is None:
            raise ValueError("Chunk cannot be None")

        if not chunk.text or not chunk.text.strip():
            raise ValueError("Chunk text cannot be empty")

        try:
            # Ensure collection exists before storing chunks
            self.create_schema(collection)

            # Get the collection
            collection = self.db_manager.get_collection(collection)

            # Prepare the object data
            object_data = self.prepare_data_object(chunk)

            # Store the object using V4 API
            self.logger.debug(f"Storing chunk: {chunk.chunk_id}")
            collection.data.insert(
                properties=object_data,
                uuid=object_data["chunk_key"],
            )

            self.logger.debug(
                f"Successfully stored chunk {chunk.chunk_id} with UUID: {object_data['chunk_key']}"
            )

            return object_data["chunk_key"]

        except WeaviateBaseError as e:
            self.logger.error(f"Failed to store chunk {chunk.chunk_id}: {str(e)}")
            raise

    def store_chunks(
        self, chunks: List[DataChunk], collection: str, batch_size: int = 100
    ) -> List[str]:
        """Store multiple DataChunks in the vector store using V4 API.

        Args:
            chunks: List of DataChunk objects to store
            collection: Name of the Weaviate class for document storage
            batch_size: Number of chunks to process in each batch

        Returns:
            List[str]: List of chunk keys (UUIDs) that were stored

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

        total_chunks = len(valid_chunks)

        try:
            # Ensure collection exists before storing chunks
            self.create_schema(collection)

            # Get the collection
            collection = self.db_manager.get_collection(collection)

            self.logger.info(
                f"Storing {total_chunks} chunks in batches of {batch_size}"
            )

            # Store UUIDs for return
            stored_uuids = []

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

                for object_data in batch_data:
                    try:
                        # Insert individual object using V4 API
                        collection.data.insert(
                            properties=object_data,
                            uuid=object_data["chunk_key"],
                        )
                        stored_uuids.append(object_data["chunk_key"])

                    except Exception as e:
                        self.logger.warning(f"Failed to insert object: {e}")
                        continue

            self.logger.info(f"Successfully stored {total_chunks} chunks")
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

        custom_meta = chunk.metadata.custom_metadata or {}
        custom_metadata_json = json.dumps(custom_meta) if custom_meta else ""

        # Extract tags value to avoid redundant dictionary lookups
        tags_value = custom_meta.get("tags", [])
        tags_string = (
            ",".join(tags_value) if isinstance(tags_value, list) else str(tags_value)
        )

        return {
            # Core fields
            "content": chunk.text,
            "chunk_id": chunk.chunk_id,
            "chunk_key": generate_uuid5(chunk.chunk_id),
            "source_document": chunk.source_document or "",
            "chunk_type": chunk.chunk_type or "",
            "created_at": chunk.metadata.created_at or "",
            # Document-specific fields
            "metadata_chunk_idx": chunk.metadata.chunk_idx,
            "metadata_chunk_size": chunk.metadata.chunk_size,
            "metadata_total_chunks": chunk.metadata.total_chunks,
            "metadata_created_at": chunk.metadata.created_at or "",
            "page_number": chunk.metadata.page_number or 0,
            "section_title": chunk.metadata.section_title or "",
            # Email-specific fields
            "email_subject": chunk.metadata.email_subject or "",
            "email_sender": chunk.metadata.email_sender or "",
            "email_recipient": chunk.metadata.email_recipient or "",
            "email_date": chunk.metadata.email_date or "",
            "email_id": chunk.metadata.email_id or "",
            "email_folder": chunk.metadata.email_folder or "",
            # Custom metadata fields
            "custom_metadata": custom_metadata_json,
            "language": custom_meta.get("language", ""),
            "domain": custom_meta.get("domain", ""),
            "confidence": custom_meta.get("confidence", 0.0),
            "tags": tags_string,
            "priority": custom_meta.get("priority", 0),
            "content_category": custom_meta.get("content_category", ""),
        }

    def get_chunk_by_id(
        self, chunk_id: str, collection: str
    ) -> Optional[RetrievalResultItem]:
        """Retrieve a specific chunk by its chunk_id using V4 API.

        Args:
            chunk_id: ID of the chunk
            collection: Name of the Weaviate class for document storage
        Returns:
            Optional[RetrievalResultItem]: Chunk data if found, None otherwise

        Raises:
            WeaviateBaseError: If retrieval operation fails
        """
        try:
            # Get the collection
            collection = self.db_manager.get_collection(collection)

            # Query using V4 API
            result = collection.query.fetch_object_by_id(
                uuid=generate_uuid5(chunk_id),
            )

            if result:
                properties = result.properties
                # Create RetrievalResultItem with structured metadata
                return RetrievalResultItem(
                    content=properties.get("content", ""),
                    chunk_id=properties.get("chunk_id", ""),
                    properties=properties,
                    metadata=RetrievalMetadata.from_properties(properties),
                )
            else:
                return None

        except WeaviateBaseError as e:
            self.logger.error(f"Failed to retrieve chunk {chunk_id}: {str(e)}")
            raise

    def delete_chunk(self, chunk_id: str, collection: str) -> bool:
        """Delete a chunk by its chunk_id using V4 API.

        Args:
            chunk_id: ID of the chunk to delete
            collection: Name of the Weaviate class for document storage
        Returns:
            bool: True if deletion was successful, False otherwise

        Raises:
            WeaviateBaseError: If deletion operation fails
        """
        try:
            # Get the collection
            collection = self.db_manager.get_collection(collection)

            # Delete by ID
            collection.data.delete_by_id(uuid=generate_uuid5(chunk_id))
            self.logger.debug(f"Successfully deleted chunk: {chunk_id}")
            return True

        except WeaviateBaseError as e:
            self.logger.error(f"Failed to delete chunk {chunk_id}: {str(e)}")
            raise

    def update_chunk(
        self, chunk_id: str, properties: Dict[str, Any], collection: str
    ) -> bool:
        """Update a chunk by its chunk_id using V4 API.

        Args:
            chunk_id: ID of the chunk to update
            properties: Properties to update
            collection: Name of the Weaviate class for document storage
        Returns:
            bool: True if update was successful, False otherwise

        Raises:
            WeaviateBaseError: If update operation fails
        """

        try:
            # Get the collection
            collection = self.db_manager.get_collection(collection)

            # Update by ID
            collection.data.update_by_id(
                uuid=generate_uuid5(chunk_id),
                properties=properties,
            )
            self.logger.debug(f"Successfully updated chunk: {chunk_id}")
            return True

        except WeaviateBaseError as e:
            self.logger.error(f"Failed to update chunk {chunk_id}: {str(e)}")
            raise

    def chunk_exists(self, chunk_id: str, collection: str) -> bool:
        """Check if a chunk exists by its chunk_id using V4 API.

        Args:
            chunk_id: ID of the chunk to check
            collection: Name of the Weaviate class for document storage
        Returns:
            bool: True if chunk exists, False otherwise

        Raises:
            WeaviateBaseError: If check operation fails
        """
        try:
            # Get the collection
            collection = self.db_manager.get_collection(collection)

            # Check if chunk exists by ID
            return collection.data.exists(uuid=generate_uuid5(chunk_id))
        except WeaviateBaseError as e:
            self.logger.error(f"Failed to check if chunk {chunk_id} exists: {str(e)}")
            raise

    def get_stats(self, collection: str) -> Dict[str, Any]:
        """Get statistics about the vector store using V4 API.

        Args:
            collection: Name of the Weaviate class for document storage

        Returns:
            Dict[str, Any]: Statistics including total objects, collection
                info, etc.

        Raises:
            WeaviateBaseError: If stats retrieval fails
        """
        try:
            # Get the collection
            collection = self.db_manager.get_collection(collection)

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
                "collection": collection,
                "collection_info": collection_info,
                "is_connected": self.is_connected(),
                "db_manager_url": self.db_manager.url,
            }

        except WeaviateBaseError as e:
            self.logger.error(f"Failed to get stats: {str(e)}")
            raise

    def clear_all(self, collection: str) -> None:
        """Clear all objects from the vector store using V4 API.

        Args:
            collection: Name of the Weaviate class for document storage

        Returns:
            None

        Raises:
            WeaviateBaseError: If clearing operation fails
        """
        try:
            self.logger.warning(f"Clearing all objects from collection: {collection}")
            self.db_manager.delete_collection(collection)
            self.logger.info(
                f"Successfully cleared all objects from collection: {collection}"
            )
        except WeaviateBaseError as e:
            self.logger.error(f"Failed to clear all objects: {str(e)}")
            raise

    def close(self) -> None:
        """Close the connection to Weaviate.

        Returns:
            None

        Raises:
            Exception: If closing operation fails
        """
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
