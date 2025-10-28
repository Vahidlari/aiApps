"""Unit tests for the EmbeddingEngine class."""

from unittest.mock import Mock, patch

import numpy as np
import pytest

from ragora import ChunkMetadata, DataChunk, EmbeddingEngine


class TestEmbeddingEngine:
    """Test cases for EmbeddingEngine class."""

    def test_init_with_valid_model(self):
        """Test initialization with a valid model name."""
        with patch(
            "ragora.ragora.core.embedding_engine.SentenceTransformer"
        ) as mock_st:
            mock_model = Mock()
            mock_st.return_value = mock_model

            engine = EmbeddingEngine(model_name="all-mpnet-base-v2")

            assert engine.model_name == "all-mpnet-base-v2"
            assert engine.embedding_dimension == 768
            assert engine.model == mock_model
            # The device should be automatically selected by device_utils
            mock_st.assert_called_once_with(
                "all-mpnet-base-v2", device="cpu", cache_folder=None
            )

    def test_init_with_invalid_model(self):
        """Test initialization with an invalid model name."""
        with pytest.raises(ValueError, match="Model 'invalid-model' not supported"):
            EmbeddingEngine(model_name="invalid-model")

    def test_supported_models(self):
        """Test that supported models are correctly defined."""
        expected_models = ["all-mpnet-base-v2", "multi-qa-MiniLM-L6-v2"]
        assert list(EmbeddingEngine.SUPPORTED_MODELS.keys()) == expected_models

        # Test model specifications
        assert EmbeddingEngine.SUPPORTED_MODELS["all-mpnet-base-v2"]["dimension"] == 768
        assert (
            EmbeddingEngine.SUPPORTED_MODELS["multi-qa-MiniLM-L6-v2"]["dimension"]
            == 384
        )

    def test_embed_text_success(self):
        """Test successful text embedding."""
        with patch(
            "ragora.ragora.core.embedding_engine.SentenceTransformer"
        ) as mock_st:
            mock_model = Mock()
            mock_embedding = np.array([0.1, 0.2, 0.3])
            mock_model.encode.return_value = mock_embedding
            mock_st.return_value = mock_model

            engine = EmbeddingEngine()
            result = engine.embed_text("test text")

            assert np.array_equal(result, mock_embedding)
            mock_model.encode.assert_called_once_with(
                "test text", convert_to_numpy=True
            )

    def test_embed_text_empty(self):
        """Test embedding with empty text."""
        with patch(
            "ragora.ragora.core.embedding_engine.SentenceTransformer"
        ) as mock_st:
            mock_model = Mock()
            mock_st.return_value = mock_model

            engine = EmbeddingEngine()

            with pytest.raises(ValueError, match="Text cannot be empty or None"):
                engine.embed_text("")

            with pytest.raises(ValueError, match="Text cannot be empty or None"):
                engine.embed_text("   ")

    def test_embed_chunk_success(self):
        """Test successful chunk embedding."""
        with patch(
            "ragora.ragora.core.embedding_engine.SentenceTransformer"
        ) as mock_st:
            mock_model = Mock()
            mock_embedding = np.array([0.1, 0.2, 0.3])
            mock_model.encode.return_value = mock_embedding
            mock_st.return_value = mock_model

            engine = EmbeddingEngine()
            metadata = ChunkMetadata(chunk_idx=1, chunk_size=10, total_chunks=1)
            chunk = DataChunk(
                text="test chunk",
                start_idx=0,
                end_idx=10,
                chunk_id="test:chunk:0:0001",
                metadata=metadata,
            )

            result = engine.embed_chunk(chunk)

            assert np.array_equal(result, mock_embedding)
            mock_model.encode.assert_called_once_with(
                "test chunk", convert_to_numpy=True
            )

    def test_embed_chunk_none(self):
        """Test embedding with None chunk."""
        with patch(
            "ragora.ragora.core.embedding_engine.SentenceTransformer"
        ) as mock_st:
            mock_model = Mock()
            mock_st.return_value = mock_model

            engine = EmbeddingEngine()

            with pytest.raises(ValueError, match="Chunk cannot be None"):
                engine.embed_chunk(None)

    def test_embed_chunks_success(self):
        """Test successful batch chunk embedding."""
        with patch(
            "ragora.ragora.core.embedding_engine.SentenceTransformer"
        ) as mock_st:
            mock_model = Mock()
            mock_embeddings = np.array([[0.1, 0.2], [0.3, 0.4]])
            mock_model.encode.return_value = mock_embeddings
            mock_st.return_value = mock_model

            engine = EmbeddingEngine()
            chunks = [
                DataChunk(
                    text="chunk 1",
                    start_idx=0,
                    end_idx=7,
                    chunk_id="test:chunk1:0:0000",
                    metadata={},
                ),
                DataChunk(
                    text="chunk 2",
                    start_idx=8,
                    end_idx=15,
                    chunk_id="test:chunk2:0:0001",
                    metadata={},
                ),
            ]

            result = engine.embed_chunks(chunks)

            assert len(result) == 2
            assert np.array_equal(result[0], np.array([0.1, 0.2]))
            assert np.array_equal(result[1], np.array([0.3, 0.4]))
            mock_model.encode.assert_called_once_with(
                ["chunk 1", "chunk 2"], convert_to_numpy=True, show_progress_bar=True
            )

    def test_embed_chunks_empty_list(self):
        """Test embedding with empty chunks list."""
        with patch(
            "ragora.ragora.core.embedding_engine.SentenceTransformer"
        ) as mock_st:
            mock_model = Mock()
            mock_st.return_value = mock_model

            engine = EmbeddingEngine()

            with pytest.raises(ValueError, match="Chunks list cannot be empty"):
                engine.embed_chunks([])

    def test_embed_texts_success(self):
        """Test successful batch text embedding."""
        with patch(
            "ragora.ragora.core.embedding_engine.SentenceTransformer"
        ) as mock_st:
            mock_model = Mock()
            mock_embeddings = np.array([[0.1, 0.2], [0.3, 0.4]])
            mock_model.encode.return_value = mock_embeddings
            mock_st.return_value = mock_model

            engine = EmbeddingEngine()
            texts = ["text 1", "text 2"]

            result = engine.embed_texts(texts)

            assert len(result) == 2
            assert np.array_equal(result[0], np.array([0.1, 0.2]))
            assert np.array_equal(result[1], np.array([0.3, 0.4]))
            mock_model.encode.assert_called_once_with(
                ["text 1", "text 2"], convert_to_numpy=True, show_progress_bar=True
            )

    def test_embed_texts_empty_list(self):
        """Test embedding with empty texts list."""
        with patch(
            "ragora.ragora.core.embedding_engine.SentenceTransformer"
        ) as mock_st:
            mock_model = Mock()
            mock_st.return_value = mock_model

            engine = EmbeddingEngine()

            with pytest.raises(ValueError, match="Texts list cannot be empty"):
                engine.embed_texts([])

    def test_get_embedding_dimension(self):
        """Test getting embedding dimension."""
        with patch(
            "ragora.ragora.core.embedding_engine.SentenceTransformer"
        ) as mock_st:
            mock_model = Mock()
            mock_st.return_value = mock_model

            engine = EmbeddingEngine(model_name="all-mpnet-base-v2")
            assert engine.get_embedding_dimension() == 768

            engine = EmbeddingEngine(model_name="multi-qa-MiniLM-L6-v2")
            assert engine.get_embedding_dimension() == 384

    def test_get_model_info(self):
        """Test getting model information."""
        with patch(
            "ragora.ragora.core.embedding_engine.SentenceTransformer"
        ) as mock_st:
            mock_model = Mock()
            mock_st.return_value = mock_model

            engine = EmbeddingEngine(model_name="all-mpnet-base-v2")
            info = engine.get_model_info()

            assert info["model_name"] == "all-mpnet-base-v2"
            assert info["dimension"] == 768
            assert "High-quality embeddings" in info["description"]
            assert info["pooling_strategy"] == "masked_mean"

    def test_similarity_calculation(self):
        """Test cosine similarity calculation."""
        with patch(
            "ragora.ragora.core.embedding_engine.SentenceTransformer"
        ) as mock_st:
            mock_model = Mock()
            mock_st.return_value = mock_model

            engine = EmbeddingEngine()

            # Test with identical vectors
            vec1 = np.array([1.0, 0.0, 0.0])
            vec2 = np.array([1.0, 0.0, 0.0])
            similarity = engine.similarity(vec1, vec2)
            assert abs(similarity - 1.0) < 1e-6

            # Test with orthogonal vectors
            vec3 = np.array([1.0, 0.0, 0.0])
            vec4 = np.array([0.0, 1.0, 0.0])
            similarity = engine.similarity(vec3, vec4)
            assert abs(similarity - 0.0) < 1e-6

            # Test with opposite vectors
            vec5 = np.array([1.0, 0.0, 0.0])
            vec6 = np.array([-1.0, 0.0, 0.0])
            similarity = engine.similarity(vec5, vec6)
            assert abs(similarity - (-1.0)) < 1e-6

    def test_similarity_method_parameter(self):
        """Test similarity method parameter selection."""
        with patch(
            "ragora.ragora.core.embedding_engine.SentenceTransformer"
        ) as mock_st:
            mock_model = Mock()
            mock_st.return_value = mock_model

            engine = EmbeddingEngine()
            vec1 = np.array([1.0, 0.0, 0.0])
            vec2 = np.array([1.0, 0.0, 0.0])

            # Test default cosine similarity
            similarity = engine.similarity(vec1, vec2)
            assert abs(similarity - 1.0) < 1e-6

            # Test explicit cosine similarity
            similarity = engine.similarity(vec1, vec2, method="cosine")
            assert abs(similarity - 1.0) < 1e-6

            # Test euclidean distance
            distance = engine.similarity(vec1, vec2, method="euclidean")
            assert abs(distance - 0.0) < 1e-6

    def test_euclidean_distance_calculation(self):
        """Test euclidean distance calculation."""
        with patch(
            "ragora.ragora.core.embedding_engine.SentenceTransformer"
        ) as mock_st:
            mock_model = Mock()
            mock_st.return_value = mock_model

            engine = EmbeddingEngine()

            # Test with identical vectors
            vec1 = np.array([1.0, 0.0, 0.0])
            vec2 = np.array([1.0, 0.0, 0.0])
            distance = engine.similarity(vec1, vec2, method="euclidean")
            assert abs(distance - 0.0) < 1e-6

            # Test with different vectors
            vec3 = np.array([1.0, 0.0, 0.0])
            vec4 = np.array([0.0, 1.0, 0.0])
            distance = engine.similarity(vec3, vec4, method="euclidean")
            assert abs(distance - np.sqrt(2)) < 1e-6

            # Test with opposite vectors
            vec5 = np.array([1.0, 0.0, 0.0])
            vec6 = np.array([-1.0, 0.0, 0.0])
            distance = engine.similarity(vec5, vec6, method="euclidean")
            assert abs(distance - 2.0) < 1e-6

    def test_invalid_similarity_method(self):
        """Test invalid similarity method."""
        with patch(
            "ragora.ragora.core.embedding_engine.SentenceTransformer"
        ) as mock_st:
            mock_model = Mock()
            mock_st.return_value = mock_model

            engine = EmbeddingEngine()
            vec1 = np.array([1.0, 0.0, 0.0])
            vec2 = np.array([1.0, 0.0, 0.0])

            with pytest.raises(ValueError, match="Invalid similarity method"):
                engine.similarity(vec1, vec2, method="invalid")

    def test_cosine_similarity_private_method(self):
        """Test private cosine similarity method."""
        with patch(
            "ragora.ragora.core.embedding_engine.SentenceTransformer"
        ) as mock_st:
            mock_model = Mock()
            mock_st.return_value = mock_model

            engine = EmbeddingEngine()
            vec1 = np.array([1.0, 0.0, 0.0])
            vec2 = np.array([1.0, 0.0, 0.0])

            similarity = engine._cosine_similarity(vec1, vec2)
            assert abs(similarity - 1.0) < 1e-6

    def test_euclidean_distance_private_method(self):
        """Test private euclidean distance method."""
        with patch(
            "ragora.ragora.core.embedding_engine.SentenceTransformer"
        ) as mock_st:
            mock_model = Mock()
            mock_st.return_value = mock_model

            engine = EmbeddingEngine()
            vec1 = np.array([1.0, 0.0, 0.0])
            vec2 = np.array([0.0, 1.0, 0.0])

            distance = engine._euclidean_distance(vec1, vec2)
            assert abs(distance - np.sqrt(2)) < 1e-6

    def test_similarity_different_dimensions(self):
        """Test similarity calculation with different dimension vectors."""
        with patch(
            "ragora.ragora.core.embedding_engine.SentenceTransformer"
        ) as mock_st:
            mock_model = Mock()
            mock_st.return_value = mock_model

            engine = EmbeddingEngine()

            vec1 = np.array([1.0, 0.0])
            vec2 = np.array([1.0, 0.0, 0.0])

            with pytest.raises(
                ValueError, match="Embeddings must have the same dimension"
            ):
                engine.similarity(vec1, vec2)

    def test_similarity_zero_vectors(self):
        """Test similarity calculation with zero vectors."""
        with patch(
            "ragora.ragora.core.embedding_engine.SentenceTransformer"
        ) as mock_st:
            mock_model = Mock()
            mock_st.return_value = mock_model

            engine = EmbeddingEngine()

            vec1 = np.array([0.0, 0.0, 0.0])
            vec2 = np.array([1.0, 0.0, 0.0])

            similarity = engine.similarity(vec1, vec2)
            assert similarity == 0.0

    def test_model_loading_error(self):
        """Test handling of model loading errors."""
        with patch(
            "ragora.ragora.core.embedding_engine.SentenceTransformer"
        ) as mock_st:
            mock_st.side_effect = Exception("Model loading failed")

            with pytest.raises(
                ImportError, match="Could not load Sentence Transformer model"
            ):
                EmbeddingEngine()

    def test_embedding_generation_error(self):
        """Test handling of embedding generation errors."""
        with patch(
            "ragora.ragora.core.embedding_engine.SentenceTransformer"
        ) as mock_st:
            mock_model = Mock()
            mock_model.encode.side_effect = Exception("Embedding generation failed")
            mock_st.return_value = mock_model

            engine = EmbeddingEngine()

            with pytest.raises(Exception, match="Embedding generation failed"):
                engine.embed_text("test text")
