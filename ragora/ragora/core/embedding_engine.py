"""Embedding engine for RAG system.

This module provides the EmbeddingEngine class that handles the conversion of
text chunks into vector embeddings using Sentence Transformers. It serves as
the bridge between processed text chunks and the vector database storage.

Key responsibilities:
- Convert text chunks into high-dimensional vector embeddings
- Support multiple embedding models (all-mpnet-base-v2, multi-qa-MiniLM-L6-v2)
- Handle batch processing for efficient embedding generation
- Provide configuration options for different use cases
- Integrate with the DataChunk objects from document preprocessing

The embedding engine uses Sentence Transformers locally to generate embeddings
without requiring external API calls, making it cost-effective and
privacy-preserving.
"""

import logging
from typing import List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from ..utils.device_utils import get_sentence_transformer_device
from .chunking import DataChunk


class EmbeddingEngine:
    """Embedding engine for converting text chunks to vector embeddings.

    This class handles the conversion of text chunks into vector embeddings
    using Sentence Transformers. It supports multiple models and provides
    efficient batch processing capabilities.

    Attributes:
        model: SentenceTransformer model instance
        model_name: Name of the loaded model
        embedding_dimension: Dimension of the generated embeddings
        logger: Logger instance for debugging and monitoring
    """

    # Supported models with their specifications
    SUPPORTED_MODELS = {
        "all-mpnet-base-v2": {
            "dimension": 768,
            "description": "High-quality embeddings for technical content",
            "pooling_strategy": "masked_mean",
        },
        "multi-qa-MiniLM-L6-v2": {
            "dimension": 384,
            "description": "Optimized for Q&A tasks, faster inference",
            "pooling_strategy": "mean",
        },
    }

    def __init__(
        self,
        model_name: str = "all-mpnet-base-v2",
        device: Optional[str] = None,
        cache_folder: Optional[str] = None,
    ):
        """Initialize the EmbeddingEngine.

        Args:
            model_name: Name of the Sentence Transformer model to use
            device: Device to run the model on ('cpu', 'cuda', 'mps', or None
                for auto). If None, will automatically select the optimal device
                for the current platform.
            cache_folder: Folder to cache the model files

        Raises:
            ValueError: If model_name is not supported
            ImportError: If sentence-transformers is not installed
        """
        if model_name not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Model '{model_name}' not supported. "
                f"Supported models: {list(self.SUPPORTED_MODELS.keys())}"
            )

        self.model_name = model_name
        self.embedding_dimension = self.SUPPORTED_MODELS[model_name]["dimension"]

        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Auto-select device if not provided
        if device is None:
            device = get_sentence_transformer_device()
            self.logger.info(f"Auto-selected device: {device}")

        try:
            # Initialize the Sentence Transformer model
            self.logger.info(
                f"Loading Sentence Transformer model: {model_name} on device: {device}"
            )
            self.model = SentenceTransformer(
                model_name, device=device, cache_folder=cache_folder
            )
            self.logger.info(
                f"Successfully loaded model: {model_name} on device: {device}"
            )

        except Exception as e:
            self.logger.error(f"Failed to load model {model_name}: {str(e)}")
            raise ImportError(f"Could not load Sentence Transformer model: {str(e)}")

    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text string.

        Args:
            text: Text to embed

        Returns:
            np.ndarray: Vector embedding of the text

        Raises:
            ValueError: If text is empty or None
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty or None")

        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            self.logger.error(f"Failed to generate embedding for text: {str(e)}")
            raise

    def embed_chunk(self, chunk: DataChunk) -> np.ndarray:
        """Generate embedding for a DataChunk object.

        Args:
            chunk: DataChunk object containing text and metadata

        Returns:
            np.ndarray: Vector embedding of the chunk text

        Raises:
            ValueError: If chunk is None or has empty text
        """
        if chunk is None:
            raise ValueError("Chunk cannot be None")

        return self.embed_text(chunk.text)

    def embed_chunks(self, chunks: List[DataChunk]) -> List[np.ndarray]:
        """Generate embeddings for multiple DataChunk objects.

        Args:
            chunks: List of DataChunk objects

        Returns:
            List[np.ndarray]: List of vector embeddings

        Raises:
            ValueError: If chunks list is empty or contains invalid chunks
        """
        if not chunks:
            raise ValueError("Chunks list cannot be empty")

        # Extract text from chunks
        texts = []
        for i, chunk in enumerate(chunks):
            if chunk is None or not chunk.text or not chunk.text.strip():
                self.logger.warning(f"Skipping invalid chunk at index {i}")
                continue
            texts.append(chunk.text)

        if not texts:
            raise ValueError("No valid text found in chunks")

        try:
            self.logger.info(f"Generating embeddings for {len(texts)} chunks")
            embeddings = self.model.encode(
                texts, convert_to_numpy=True, show_progress_bar=True
            )

            # Convert to list of numpy arrays
            embedding_list = [embeddings[i] for i in range(len(embeddings))]

            self.logger.info(f"Successfully generated {len(embedding_list)} embeddings")
            return embedding_list

        except Exception as e:
            self.logger.error(f"Failed to generate embeddings for chunks: {str(e)}")
            raise

    def embed_texts(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for a list of text strings.

        Args:
            texts: List of text strings to embed

        Returns:
            List[np.ndarray]: List of vector embeddings

        Raises:
            ValueError: If texts list is empty or contains invalid strings
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")

        # Filter out empty texts
        valid_texts = [text for text in texts if text and text.strip()]

        if not valid_texts:
            raise ValueError("No valid text found in texts list")

        try:
            self.logger.info(f"Generating embeddings for {len(valid_texts)} texts")
            embeddings = self.model.encode(
                valid_texts, convert_to_numpy=True, show_progress_bar=True
            )

            # Convert to list of numpy arrays
            embedding_list = [embeddings[i] for i in range(len(embeddings))]

            self.logger.info(f"Successfully generated {len(embedding_list)} embeddings")
            return embedding_list

        except Exception as e:
            self.logger.error(f"Failed to generate embeddings for texts: {str(e)}")
            raise

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this engine.

        Returns:
            int: Dimension of the embeddings
        """
        return self.embedding_dimension

    def get_model_info(self) -> dict:
        """Get information about the current model.

        Returns:
            dict: Model information including name, dimension, and
                description
        """
        return {
            "model_name": self.model_name,
            "dimension": self.embedding_dimension,
            "description": self.SUPPORTED_MODELS[self.model_name]["description"],
            "pooling_strategy": self.SUPPORTED_MODELS[self.model_name][
                "pooling_strategy"
            ],
        }

    def similarity(
        self, embedding1: np.ndarray, embedding2: np.ndarray, method: str = "cosine"
    ) -> float:
        """Calculate similarity between two embeddings using specified method.

        This function provides a unified interface for different similarity
        measures, allowing you to choose the most appropriate method for your
        use case.

        Method Comparison:
        - "cosine": Measures angular similarity (direction-based)
          * Range: [-1, 1] where higher values = more similar
          * Best for: Semantic similarity, normalized vectors
          * Interpretation: 1.0=identical, 0.0=unrelated, -1.0=opposite

        - "euclidean": Measures geometric distance (magnitude-based)
          * Range: [0, ∞) where lower values = more similar
          * Best for: Absolute differences, magnitude-sensitive comparisons
          * Interpretation: 0.0=identical, higher values=more different

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            method: Similarity method to use ("cosine" or "euclidean")

        Returns:
            float: Similarity score
            - For cosine: score between -1 and 1 (higher = more similar)
            - For euclidean: distance between 0 and ∞ (lower = more similar)

        Raises:
            ValueError: If embeddings have different dimensions or invalid
                method

        Examples:
            >>> engine = EmbeddingEngine()
            >>> vec1 = np.array([1.0, 0.0, 0.0])
            >>> vec2 = np.array([0.0, 1.0, 0.0])
            >>>
            >>> # Cosine similarity (default)
            >>> engine.similarity(vec1, vec2)  # Returns 0.0 (orthogonal)
            >>>
            >>> # Euclidean distance
            >>> engine.similarity(vec1, vec2, method="euclidean")
            >>> # Returns 1.414
        """
        if embedding1.shape != embedding2.shape:
            raise ValueError("Embeddings must have the same dimension")

        if method.lower() == "cosine":
            return self._cosine_similarity(embedding1, embedding2)
        elif method.lower() == "euclidean":
            return self._euclidean_distance(embedding1, embedding2)
        else:
            raise ValueError(
                f"Invalid similarity method '{method}'. "
                "Supported methods: 'cosine', 'euclidean'"
            )

    def _cosine_similarity(
        self, embedding1: np.ndarray, embedding2: np.ndarray
    ) -> float:
        """Calculate cosine similarity between two embeddings.

        Cosine similarity measures the cosine of the angle between two vectors,
        providing a measure of semantic similarity regardless of vector
        magnitude.

        Value Interpretation:
        - +1.0: Identical vectors (0° angle) - maximally similar
        -  0.0: Orthogonal vectors (90° angle) - completely unrelated
        - -1.0: Opposite vectors (180° angle) - maximally dissimilar/
          contradictory

        Examples:
        - [1,0,0] vs [1,0,0] → 1.0 (identical)
        - [1,0,0] vs [0,1,0] → 0.0 (orthogonal/unrelated)
        - [1,0,0] vs [-1,0,0] → -1.0 (opposite/contradictory)

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            float: Cosine similarity score between -1 and 1
                (higher values = more similar)
        """
        # Calculate cosine similarity
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)
        return float(similarity)

    def _euclidean_distance(
        self, embedding1: np.ndarray, embedding2: np.ndarray
    ) -> float:
        """Calculate Euclidean distance between two embeddings.

        Euclidean distance measures the straight-line distance between two
        points in the embedding space, providing a measure of absolute
        difference.

        Value Interpretation:
        - 0.0: Identical vectors - maximally similar
        - >0.0: Distance between vectors - lower values = more similar
        - Higher values indicate greater dissimilarity

        Examples:
        - [1,0,0] vs [1,0,0] → 0.0 (identical)
        - [1,0,0] vs [0,1,0] → 1.414 (orthogonal)
        - [1,0,0] vs [-1,0,0] → 2.0 (opposite)

        Note: Unlike cosine similarity, euclidean distance is sensitive to
        vector magnitude and measures absolute differences rather than
        directional similarity.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            float: Euclidean distance (lower values = more similar)
        """
        distance = np.linalg.norm(embedding1 - embedding2)
        return float(distance)
