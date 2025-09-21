"""Integration tests for the complete RAG pipeline.

This module contains comprehensive integration tests that test the complete
RAG system workflow, including document processing, storage, retrieval,
and querying operations.

Test coverage includes:
- End-to-end document processing pipeline
- Complete RAG system workflow
- Component integration and communication
- Real-world usage scenarios
- Performance and reliability testing
- Error handling across components
"""

import os
import tempfile
from unittest.mock import MagicMock, Mock, patch

import pytest
from ragnarock import ChunkMetadata, DataChunk, RAGSystem


class TestRAGPipeline:
    """Integration test suite for the complete RAG pipeline."""

    @pytest.fixture
    def sample_latex_document(self):
        """Create a sample LaTeX document for testing."""
        return r"""
\documentclass{article}
\usepackage{amsmath}
\begin{document}

\title{Test Document}
\author{Test Author}
\date{\today}
\maketitle

\section{Introduction}
This is a test document for the RAG system. It contains mathematical equations and citations.

\section{Mathematical Content}
The famous equation is:
\begin{equation}
E = mc^2
\end{equation}

This equation was derived by Einstein in 1905 \cite{einstein1905}.

\section{Conclusion}
The theory of relativity revolutionized physics.

\begin{thebibliography}{9}
\bibitem{einstein1905}
Einstein, A. (1905). On the Electrodynamics of Moving Bodies. Annalen der Physik, 17(10), 891-921.
\end{thebibliography}

\end{document}
"""

    @pytest.fixture
    def sample_chunks(self):
        """Create sample chunks for testing."""
        return [
            DataChunk(
                text="This is a test document for the RAG system. It contains mathematical equations and citations.",
                start_idx=0,
                end_idx=100,
                metadata=ChunkMetadata(
                    chunk_id=1,
                    chunk_size=100,
                    total_chunks=3,
                    source_document="test_document.tex",
                    page_number=1,
                    section_title="Introduction",
                    chunk_type="text",
                ),
                chunk_id="intro_001",
                source_document="test_document.tex",
                chunk_type="text",
            ),
            DataChunk(
                text="The famous equation is: E = mc²",
                start_idx=101,
                end_idx=150,
                metadata=ChunkMetadata(
                    chunk_id=2,
                    chunk_size=49,
                    total_chunks=3,
                    source_document="test_document.tex",
                    page_number=2,
                    section_title="Mathematical Content",
                    chunk_type="equation",
                ),
                chunk_id="math_001",
                source_document="test_document.tex",
                chunk_type="equation",
            ),
            DataChunk(
                text="Einstein, A. (1905). On the Electrodynamics of Moving Bodies. Annalen der Physik, 17(10), 891-921.",
                start_idx=151,
                end_idx=250,
                metadata=ChunkMetadata(
                    chunk_id=3,
                    chunk_size=99,
                    total_chunks=3,
                    source_document="test_document.tex",
                    page_number=3,
                    section_title="Bibliography",
                    chunk_type="citation",
                ),
                chunk_id="citation_001",
                source_document="test_document.tex",
                chunk_type="citation",
            ),
        ]

    @patch("ragnarock.core.rag_system.EmbeddingEngine")
    @patch("ragnarock.core.rag_system.VectorStore")
    @patch("ragnarock.core.rag_system.Retriever")
    @patch("ragnarock.core.rag_system.DocumentPreprocessor")
    @patch("ragnarock.core.rag_system.DataChunker")
    def test_complete_rag_system_initialization(
        self,
        mock_data_chunker,
        mock_document_preprocessor,
        mock_retriever,
        mock_vector_store,
        mock_embedding_engine,
    ):
        """Test complete RAG system initialization."""
        # Setup mocks
        mock_embedding_engine.return_value = Mock()
        mock_vector_store.return_value = Mock()
        mock_retriever.return_value = Mock()
        mock_document_preprocessor.return_value = Mock()
        mock_data_chunker.return_value = Mock()

        # Test
        rag = RAGSystem(
            weaviate_url="http://localhost:8080",
            class_name="TestDocument",
            embedding_model="all-mpnet-base-v2",
            chunk_size=768,
            chunk_overlap=100,
        )

        # Assertions
        assert rag.is_initialized is True
        assert rag.vector_store is not None
        assert rag.retriever is not None
        assert rag.embedding_engine is not None
        assert rag.document_preprocessor is not None
        assert rag.data_chunker is not None

    @patch("ragnarock.core.rag_system.EmbeddingEngine")
    @patch("ragnarock.core.rag_system.VectorStore")
    @patch("ragnarock.core.rag_system.Retriever")
    @patch("ragnarock.core.rag_system.DocumentPreprocessor")
    @patch("ragnarock.core.rag_system.DataChunker")
    def test_document_processing_pipeline(
        self,
        mock_data_chunker,
        mock_document_preprocessor,
        mock_retriever,
        mock_vector_store,
        mock_embedding_engine,
        sample_latex_document,
        sample_chunks,
    ):
        """Test complete document processing pipeline."""
        # Setup mocks
        mock_embedding_engine.return_value = Mock()
        mock_vector_store.return_value = Mock()
        mock_retriever.return_value = Mock()
        mock_document_preprocessor.return_value = Mock()
        mock_data_chunker.return_value = Mock()

        # Setup document processing mocks
        mock_processed_doc = Mock()
        mock_document_preprocessor.return_value.preprocess_document.return_value = (
            mock_processed_doc
        )
        mock_data_chunker.return_value.chunk_document.return_value = sample_chunks
        mock_vector_store.return_value.store_chunks.return_value = [
            "uuid1",
            "uuid2",
            "uuid3",
        ]

        # Create RAG system
        rag = RAGSystem()

        # Create temporary LaTeX file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", delete=False) as f:
            f.write(sample_latex_document)
            temp_path = f.name

        try:
            # Test document processing
            result = rag.process_document(temp_path)

            # Assertions
            assert result == ["uuid1", "uuid2", "uuid3"]
            mock_document_preprocessor.return_value.preprocess_document.assert_called_once_with(
                temp_path
            )
            mock_data_chunker.return_value.chunk_document.assert_called_once_with(
                mock_processed_doc
            )
            mock_vector_store.return_value.store_chunks.assert_called_once_with(
                sample_chunks
            )

        finally:
            os.unlink(temp_path)

    @patch("ragnarock.core.rag_system.EmbeddingEngine")
    @patch("ragnarock.core.rag_system.VectorStore")
    @patch("ragnarock.core.rag_system.Retriever")
    @patch("ragnarock.core.rag_system.DocumentPreprocessor")
    @patch("ragnarock.core.rag_system.DataChunker")
    def test_query_processing_pipeline(
        self,
        mock_data_chunker,
        mock_document_preprocessor,
        mock_retriever,
        mock_vector_store,
        mock_embedding_engine,
        sample_chunks,
    ):
        """Test complete query processing pipeline."""
        # Setup mocks
        mock_embedding_engine.return_value = Mock()
        mock_vector_store.return_value = Mock()
        mock_retriever.return_value = Mock()
        mock_document_preprocessor.return_value = Mock()
        mock_data_chunker.return_value = Mock()

        # Setup query processing mocks
        mock_search_results = [
            {
                "content": "The famous equation is: E = mc²",
                "chunk_id": "math_001",
                "source_document": "test_document.tex",
                "chunk_type": "equation",
                "metadata": {"page_number": 2, "section_title": "Mathematical Content"},
                "similarity_score": 0.95,
            },
            {
                "content": "This equation was derived by Einstein in 1905",
                "chunk_id": "citation_001",
                "source_document": "test_document.tex",
                "chunk_type": "citation",
                "metadata": {"page_number": 3, "section_title": "Bibliography"},
                "similarity_score": 0.85,
            },
        ]
        mock_retriever.return_value.search_hybrid.return_value = mock_search_results

        # Create RAG system
        rag = RAGSystem()

        # Test query processing
        result = rag.query(
            "What is Einstein's famous equation?",
            search_type="hybrid",
            top_k=5,
        )

        # Assertions
        assert result["question"] == "What is Einstein's famous equation?"
        assert result["search_type"] == "hybrid"
        assert result["num_chunks"] == 2
        assert result["retrieved_chunks"] == mock_search_results
        assert "test_document.tex" in result["chunk_sources"]
        assert "equation" in result["chunk_types"]
        assert "citation" in result["chunk_types"]
        assert abs(result["avg_similarity"] - 0.9) < 0.01  # (0.95 + 0.85) / 2
        assert result["max_similarity"] == 0.95

        # Verify retriever was called correctly
        mock_retriever.return_value.search_hybrid.assert_called_once_with(
            "What is Einstein's famous equation?", top_k=5
        )

    @patch("ragnarock.core.rag_system.EmbeddingEngine")
    @patch("ragnarock.core.rag_system.VectorStore")
    @patch("ragnarock.core.rag_system.Retriever")
    @patch("ragnarock.core.rag_system.DocumentPreprocessor")
    @patch("ragnarock.core.rag_system.DataChunker")
    def test_system_statistics_integration(
        self,
        mock_data_chunker,
        mock_document_preprocessor,
        mock_retriever,
        mock_vector_store,
        mock_embedding_engine,
    ):
        """Test system statistics integration."""
        # Setup mocks
        mock_embedding_engine.return_value = Mock()
        mock_vector_store.return_value = Mock()
        mock_retriever.return_value = Mock()
        mock_document_preprocessor.return_value = Mock()
        mock_data_chunker.return_value = Mock()

        # Setup statistics mocks
        mock_vector_store.return_value.get_stats.return_value = {
            "total_objects": 150,
            "class_name": "Document",
            "is_connected": True,
        }
        mock_retriever.return_value.get_retrieval_stats.return_value = {
            "vector_store_stats": {},
            "embedding_model": "all-mpnet-base-v2",
            "embedding_dimension": 768,
        }
        mock_embedding_engine.return_value.get_model_info.return_value = {
            "model_name": "all-mpnet-base-v2",
            "dimension": 768,
        }

        # Create RAG system
        rag = RAGSystem()

        # Test system statistics
        stats = rag.get_system_stats()

        # Assertions
        assert stats["system_initialized"] is True
        assert stats["vector_store"]["total_objects"] == 150
        assert stats["embedding_engine"]["model_name"] == "all-mpnet-base-v2"
        assert "components" in stats
        assert "retrieval" in stats

    @patch("ragnarock.core.rag_system.EmbeddingEngine")
    @patch("ragnarock.core.rag_system.VectorStore")
    @patch("ragnarock.core.rag_system.Retriever")
    @patch("ragnarock.core.rag_system.DocumentPreprocessor")
    @patch("ragnarock.core.rag_system.DataChunker")
    def test_error_handling_integration(
        self,
        mock_data_chunker,
        mock_document_preprocessor,
        mock_retriever,
        mock_vector_store,
        mock_embedding_engine,
    ):
        """Test error handling across components."""
        # Setup mocks
        mock_embedding_engine.return_value = Mock()
        mock_vector_store.return_value = Mock()
        mock_retriever.return_value = Mock()
        mock_document_preprocessor.return_value = Mock()
        mock_data_chunker.return_value = Mock()

        # Setup error conditions
        mock_retriever.return_value.search_similar.side_effect = Exception(
            "Search failed"
        )

        # Create RAG system
        rag = RAGSystem()

        # Test error handling
        with pytest.raises(Exception, match="Search failed"):
            rag.search_similar("test query")

    @patch("ragnarock.core.rag_system.EmbeddingEngine")
    @patch("ragnarock.core.rag_system.VectorStore")
    @patch("ragnarock.core.rag_system.Retriever")
    @patch("ragnarock.core.rag_system.DocumentPreprocessor")
    @patch("ragnarock.core.rag_system.DataChunker")
    def test_context_manager_integration(
        self,
        mock_data_chunker,
        mock_document_preprocessor,
        mock_retriever,
        mock_vector_store,
        mock_embedding_engine,
    ):
        """Test context manager integration."""
        # Setup mocks
        mock_embedding_engine.return_value = Mock()
        mock_vector_store.return_value = Mock()
        mock_retriever.return_value = Mock()
        mock_document_preprocessor.return_value = Mock()
        mock_data_chunker.return_value = Mock()

        # Test context manager
        with RAGSystem() as rag:
            assert rag.is_initialized is True
            assert rag.vector_store is not None
            assert rag.retriever is not None

        # Verify cleanup
        assert rag.is_initialized is False

    @patch("ragnarock.core.rag_system.EmbeddingEngine")
    @patch("ragnarock.core.rag_system.VectorStore")
    @patch("ragnarock.core.rag_system.Retriever")
    @patch("ragnarock.core.rag_system.DocumentPreprocessor")
    @patch("ragnarock.core.rag_system.DataChunker")
    def test_component_communication(
        self,
        mock_data_chunker,
        mock_document_preprocessor,
        mock_retriever,
        mock_vector_store,
        mock_embedding_engine,
    ):
        """Test communication between components."""
        # Setup mocks
        mock_embedding_engine.return_value = Mock()
        mock_vector_store.return_value = Mock()
        mock_retriever.return_value = Mock()
        mock_document_preprocessor.return_value = Mock()
        mock_data_chunker.return_value = Mock()

        # Create RAG system
        rag = RAGSystem()

        # Test that components are properly connected
        assert hasattr(rag.retriever, "vector_store")
        assert hasattr(rag.retriever, "embedding_engine")
        assert hasattr(rag.vector_store, "embedding_engine")
        assert rag.is_initialized is True

    @patch("ragnarock.core.rag_system.EmbeddingEngine")
    @patch("ragnarock.core.rag_system.VectorStore")
    @patch("ragnarock.core.rag_system.Retriever")
    @patch("ragnarock.core.rag_system.DocumentPreprocessor")
    @patch("ragnarock.core.rag_system.DataChunker")
    def test_performance_characteristics(
        self,
        mock_data_chunker,
        mock_document_preprocessor,
        mock_retriever,
        mock_vector_store,
        mock_embedding_engine,
    ):
        """Test performance characteristics of the system."""
        # Setup mocks
        mock_embedding_engine.return_value = Mock()
        mock_vector_store.return_value = Mock()
        mock_retriever.return_value = Mock()
        mock_document_preprocessor.return_value = Mock()
        mock_data_chunker.return_value = Mock()

        # Create RAG system
        rag = RAGSystem()

        # Test that system is ready for operations
        assert rag.is_initialized is True
        assert hasattr(rag, "vector_store")
        assert hasattr(rag, "retriever")
        assert hasattr(rag, "embedding_engine")
        assert hasattr(rag, "document_preprocessor")
        assert hasattr(rag, "data_chunker")

    @patch("ragnarock.core.rag_system.EmbeddingEngine")
    @patch("ragnarock.core.rag_system.VectorStore")
    @patch("ragnarock.core.rag_system.Retriever")
    @patch("ragnarock.core.rag_system.DocumentPreprocessor")
    @patch("ragnarock.core.rag_system.DataChunker")
    def test_configuration_validation(
        self,
        mock_data_chunker,
        mock_document_preprocessor,
        mock_retriever,
        mock_vector_store,
        mock_embedding_engine,
    ):
        """Test configuration validation."""
        # Setup mocks
        mock_embedding_engine.return_value = Mock()
        mock_vector_store.return_value = Mock()
        mock_retriever.return_value = Mock()
        mock_document_preprocessor.return_value = Mock()
        mock_data_chunker.return_value = Mock()

        # Test with custom configuration
        rag = RAGSystem(
            weaviate_url="http://custom:8080",
            class_name="CustomDocument",
            embedding_model="custom-model",
            chunk_size=512,
            chunk_overlap=50,
        )

        # Assertions
        assert rag.is_initialized is True
        assert rag.vector_store is not None
        assert rag.retriever is not None
        assert rag.embedding_engine is not None
        assert rag.document_preprocessor is not None
        assert rag.data_chunker is not None
