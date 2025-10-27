"""Database management layer for RAG system using Weaviate.

This module provides the DatabaseManager class that handles low-level
database operations and connection management. It serves as the
infrastructure layer that both VectorStore and Retriever use for
database access.

Key responsibilities:
- Initialize and manage Weaviate client connections
- Provide collection access and management
- Handle connection testing and health checks
- Manage database schema operations
- Provide clean abstraction over Weaviate client operations

The DatabaseManager focuses solely on infrastructure concerns,
allowing higher layers to focus on business logic.
"""

import logging
from typing import Any, Dict, List

from weaviate import WeaviateClient
from weaviate.connect import ConnectionParams
from weaviate.exceptions import WeaviateBaseError


class DatabaseManager:
    """Database management layer for Weaviate operations.

    This class provides a clean abstraction over Weaviate client operations,
    focusing on infrastructure concerns like connection management, collection
    access, and basic database operations.

    Attributes:
        client: Weaviate client instance
        url: Weaviate server URL
        grpc_port: gRPC port for Weaviate connection
        timeout: Connection timeout in seconds
        retry_attempts: Number of retry attempts for failed operations
        is_connected: Boolean indicating if connection to Weaviate is active
        logger: Logger instance for debugging and monitoring
    """

    def __init__(
        self,
        url: str = "http://localhost:8080",
        grpc_port: int = 50051,
        timeout: int = 60,
        retry_attempts: int = 3,
    ):
        """Initialize the DatabaseManager with Weaviate connection.

        Args:
            url: Weaviate server URL
            grpc_port: gRPC port for Weaviate connection
            timeout: Connection timeout in seconds
            retry_attempts: Number of retry attempts for failed operations

        Raises:
            ConnectionError: If unable to connect to Weaviate
            ValueError: If invalid parameters are provided
        """
        self.url = url
        self.grpc_port = grpc_port
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.is_connected = False

        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Initialize Weaviate client
        try:
            self.logger.info(f"Connecting to Weaviate at {url}")
            # Parse URL to extract host and port
            connection_param = ConnectionParams.from_url(
                url=url,
                # Keep gRPC port but it will fail gracefully
                grpc_port=grpc_port,
            )
            self.client = WeaviateClient(connection_param)
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

    def _normalize_collection_name(self, name: str) -> str:
        """Normalize collection name to Weaviate's naming convention.

        Weaviate automatically capitalizes the first letter of collection
        names. This method ensures we match Weaviate's expected format.

        Args:
            name: The original collection name

        Returns:
            str: Collection name with first letter capitalized

        Raises:
            ValueError: If name is empty
        """
        if not name or not name.strip():
            raise ValueError("Collection name cannot be empty")

        # Capitalize first letter, keep rest as-is
        return name[0].upper() + name[1:]

    def is_ready(self) -> bool:
        """Check if the database is ready for operations.

        Returns:
            bool: True if database is ready
        """
        try:
            return self.client.is_ready()
        except Exception as e:
            self.logger.error(f"Database readiness check failed: {str(e)}")
            return False

    def get_collection(self, name: str):
        """Get a collection reference by name.

        Args:
            name: Name of the collection to retrieve

        Returns:
            Collection object for the specified name

        Raises:
            ValueError: If collection name is empty
            WeaviateBaseError: If collection access fails
        """
        if not name or not name.strip():
            raise ValueError("Collection name cannot be empty")

        try:
            # Normalize name to Weaviate's naming convention
            normalized_name = self._normalize_collection_name(name)
            collection = self.client.collections.get(normalized_name)
            self.logger.debug(f"Retrieved collection: {normalized_name}")
            return collection
        except WeaviateBaseError as e:
            self.logger.error(f"Failed to get collection {name}: {str(e)}")
            raise

    def create_collection(
        self,
        name: str,
        description: str = "",
        vectorizer_config=None,
        properties: List[Dict[str, Any]] = None,
    ):
        """Create a new collection with the specified configuration.

        Args:
            name: Name of the collection to create
            description: Description of the collection
            vectorizer_config: Vectorizer configuration
            properties: List of property configurations

        Returns:
            Created collection object

        Raises:
            ValueError: If collection name is empty
            WeaviateBaseError: If collection creation fails
        """
        if not name or not name.strip():
            raise ValueError("Collection name cannot be empty")

        try:
            # Normalize name to Weaviate's naming convention
            normalized_name = self._normalize_collection_name(name)
            self.logger.info(f"Creating collection: {normalized_name}")

            # Create the collection using V4 API
            collection = self.client.collections.create(
                name=normalized_name,
                description=description,
                vectorizer_config=vectorizer_config,
                properties=properties or [],
            )

            self.logger.info(f"Successfully created collection: {normalized_name}")
            return collection

        except WeaviateBaseError as e:
            self.logger.error(f"Failed to create collection {name}: {str(e)}")
            raise

    def delete_collection(self, name: str) -> bool:
        """Delete a collection by name.

        Args:
            name: Name of the collection to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            ValueError: If collection name is empty
            WeaviateBaseError: If collection deletion fails
        """
        if not name or not name.strip():
            raise ValueError("Collection name cannot be empty")

        try:
            # Normalize name to Weaviate's naming convention
            normalized_name = self._normalize_collection_name(name)
            self.logger.info(f"Deleting collection: {normalized_name}")
            self.client.collections.delete(normalized_name)
            self.logger.info(f"Successfully deleted collection: {normalized_name}")
            return True

        except WeaviateBaseError as e:
            self.logger.error(f"Failed to delete collection {name}: {str(e)}")
            raise

    def list_collections(self) -> List[str]:
        """List all available collections.

        Returns:
            List[str]: List of collection names

        Raises:
            WeaviateBaseError: If listing collections fails
        """
        try:
            collections = self.client.collections.list_all()
            collection_names = list(collections.keys())
            self.logger.debug(f"Found {len(collection_names)} collections")
            return collection_names
        except WeaviateBaseError as e:
            self.logger.error(f"Failed to list collections: {str(e)}")
            raise

    def collection_exists(self, name: str) -> bool:
        """Check if a collection exists.

        Args:
            name: Name of the collection to check

        Returns:
            bool: True if collection exists

        Raises:
            ValueError: If collection name is empty
        """
        if not name or not name.strip():
            raise ValueError("Collection name cannot be empty")

        try:
            # Normalize the name to Weaviate's naming convention
            normalized_name = self._normalize_collection_name(name)
            collections = self.list_collections()
            return normalized_name in collections
        except Exception as e:
            self.logger.error(f"Failed to check if collection {name} exists: {str(e)}")
            return False

    def get_client(self) -> WeaviateClient:
        """Get the underlying Weaviate client.

        Returns:
            WeaviateClient: The underlying client instance
        """
        return self.client

    def close(self) -> None:
        """Close the connection to Weaviate."""
        try:
            if hasattr(self, "client") and self.client:
                # Weaviate client doesn't have an explicit close method
                # but we can mark the connection as closed
                self.is_connected = False
                self.logger.info("Database manager connection closed")
        except Exception as e:
            self.logger.error(f"Error closing database manager: {str(e)}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
