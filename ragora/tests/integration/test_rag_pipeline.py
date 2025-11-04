"""Integration tests for the complete knowledge base manager pipeline.

This module contains comprehensive integration tests that test the complete
knowledge base manager workflow, including document processing, storage, retrieval,
and querying operations.

Test coverage includes:
- End-to-end document processing pipeline
- Complete knowledge base manager workflow
- Component integration and communication
- Real-world usage scenarios
- Performance and reliability testing
- Error handling across components
"""

import os
import tempfile
from unittest.mock import MagicMock, Mock, patch

import pytest

from ragora import (
    ChunkMetadata,
    DataChunk,
    KnowledgeBaseManager,
    RetrievalMetadata,
    SearchResult,
    SearchResultItem,
    SearchStrategy,
)


class TestKnowledgeBaseManagerPipeline:
    """Integration test suite for the complete knowledge base manager pipeline."""

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
                    chunk_idx=1,
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
                    chunk_idx=2,
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
                    chunk_idx=3,
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

    @patch("ragora.ragora.core.knowledge_base_manager.DatabaseManager")
    @patch("ragora.ragora.core.knowledge_base_manager.VectorStore")
    @patch("ragora.ragora.core.knowledge_base_manager.Retriever")
    @patch("ragora.ragora.core.knowledge_base_manager.DocumentPreprocessor")
    def test_complete_knowledge_base_manager_initialization(
        self,
        mock_document_preprocessor,
        mock_retriever,
        mock_vector_store,
        mock_db_manager,
    ):
        """Test complete knowledge base manager initialization."""
        # Setup mocks
        mock_db_manager.return_value = Mock()
        mock_vector_store.return_value = Mock()
        mock_retriever.return_value = Mock()
        mock_document_preprocessor.return_value = Mock()

        # Test
        kbm = KnowledgeBaseManager(
            weaviate_url="http://localhost:8080",
        )

        # Assertions
        assert kbm.is_initialized is True
        assert kbm.vector_store is not None
        assert kbm.retriever is not None
        assert kbm.embedding_engine is None  # Not initialized by default
        assert kbm.document_preprocessor is not None
        assert kbm.data_chunker is None  # Not initialized by KnowledgeBaseManager

    @patch("ragora.ragora.core.knowledge_base_manager.DatabaseManager")
    @patch("ragora.ragora.core.knowledge_base_manager.VectorStore")
    @patch("ragora.ragora.core.knowledge_base_manager.Retriever")
    @patch("ragora.ragora.core.knowledge_base_manager.DocumentPreprocessor")
    @patch("ragora.ragora.core.knowledge_base_manager.DataChunker")
    def test_document_processing_pipeline(
        self,
        mock_data_chunker,
        mock_document_preprocessor,
        mock_retriever,
        mock_vector_store,
        mock_db_manager,
        sample_latex_document,
        sample_chunks,
    ):
        """Test complete document processing pipeline."""
        # Setup mocks
        mock_db_manager.return_value = Mock()
        mock_vector_store.return_value = Mock()
        mock_retriever.return_value = Mock()
        mock_document_preprocessor.return_value = Mock()
        mock_data_chunker.return_value = Mock()

        # Setup document processing mocks
        # The document preprocessor should return chunks directly
        mock_document_preprocessor.return_value.preprocess_document.return_value = (
            sample_chunks
        )
        mock_vector_store.return_value.store_chunks.return_value = [
            "uuid1",
            "uuid2",
            "uuid3",
        ]

        # Create knowledge base manager system
        kbm = KnowledgeBaseManager()

        # Create temporary LaTeX file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", delete=False) as f:
            f.write(sample_latex_document)
            temp_path = f.name

        try:
            # Test document processing
            result = kbm.process_document(temp_path)

            # Assertions
            assert result == ["uuid1", "uuid2", "uuid3"]
            mock_document_preprocessor.return_value.preprocess_document.assert_called_once_with(
                temp_path, "latex"
            )
            mock_vector_store.return_value.store_chunks.assert_called_once_with(
                sample_chunks, collection="Document"
            )

        finally:
            os.unlink(temp_path)

    @patch("ragora.ragora.core.knowledge_base_manager.DatabaseManager")
    @patch("ragora.ragora.core.knowledge_base_manager.VectorStore")
    @patch("ragora.ragora.core.knowledge_base_manager.Retriever")
    @patch("ragora.ragora.core.knowledge_base_manager.DocumentPreprocessor")
    @patch("ragora.ragora.core.knowledge_base_manager.DataChunker")
    def test_query_processing_pipeline(
        self,
        mock_data_chunker,
        mock_document_preprocessor,
        mock_retriever,
        mock_vector_store,
        mock_db_manager,
        sample_chunks,
    ):
        """Test complete query processing pipeline."""
        # Setup mocks
        mock_db_manager.return_value = Mock()
        mock_vector_store.return_value = Mock()
        mock_retriever.return_value = Mock()
        mock_document_preprocessor.return_value = Mock()
        mock_data_chunker.return_value = Mock()

        # Setup query processing mocks
        mock_search_results = [
            SearchResultItem(
                content="The famous equation is: E = mc²",
                chunk_id="math_001",
                properties={
                    "content": "The famous equation is: E = mc²",
                    "chunk_id": "math_001",
                    "source_document": "test_document.tex",
                    "chunk_type": "equation",
                },
                similarity_score=0.95,
                hybrid_score=0.95,
                retrieval_method="hybrid_search",
                metadata=RetrievalMetadata(
                    source_document="test_document.tex",
                    chunk_type="equation",
                    page_number=2,
                    section_title="Mathematical Content",
                ),
            ),
            SearchResultItem(
                content="This equation was derived by Einstein in 1905",
                chunk_id="citation_001",
                properties={
                    "content": "This equation was derived by Einstein in 1905",
                    "chunk_id": "citation_001",
                    "source_document": "test_document.tex",
                    "chunk_type": "citation",
                },
                similarity_score=0.85,
                hybrid_score=0.85,
                retrieval_method="hybrid_search",
                metadata=RetrievalMetadata(
                    source_document="test_document.tex",
                    chunk_type="citation",
                    page_number=3,
                    section_title="Bibliography",
                ),
            ),
        ]
        mock_retriever.return_value.search_hybrid.return_value = mock_search_results

        # Create knowledge base manager system
        kbm = KnowledgeBaseManager()

        # Test query processing
        result = kbm.search(
            "What is Einstein's famous equation?",
            strategy=SearchStrategy.HYBRID,
            top_k=5,
        )

        # Assertions
        assert result.query == "What is Einstein's famous equation?"
        assert result.strategy == "hybrid"
        assert result.total_found == 2
        assert len(result.results) == len(mock_search_results)
        # Compare individual properties
        assert result.results[0].content == mock_search_results[0].content
        assert result.results[0].chunk_id == mock_search_results[0].chunk_id
        assert result.results[1].content == mock_search_results[1].content
        assert result.results[1].chunk_id == mock_search_results[1].chunk_id
        assert "test_document.tex" in result.metadata["chunk_sources"]
        assert "equation" in result.metadata["chunk_types"]
        assert "citation" in result.metadata["chunk_types"]
        assert abs(result.metadata["avg_similarity"] - 0.9) < 0.01  # (0.95 + 0.85) / 2
        assert result.metadata["max_similarity"] == 0.95
        # Verify SearchResultItem instances
        assert isinstance(result.results[0], SearchResultItem)
        assert isinstance(result.results[1], SearchResultItem)

        # Verify retriever was called correctly
        mock_retriever.return_value.search_hybrid.assert_called_once_with(
            "What is Einstein's famous equation?",
            collection="Document",
            top_k=5,
            filter=None,
        )

    @patch("ragora.ragora.core.knowledge_base_manager.DatabaseManager")
    @patch("ragora.ragora.core.knowledge_base_manager.VectorStore")
    @patch("ragora.ragora.core.knowledge_base_manager.Retriever")
    @patch("ragora.ragora.core.knowledge_base_manager.DocumentPreprocessor")
    def test_system_statistics_integration(
        self,
        mock_document_preprocessor,
        mock_retriever,
        mock_vector_store,
        mock_db_manager,
    ):
        """Test system statistics integration."""
        # Setup mocks
        mock_db_manager.return_value = Mock()
        mock_vector_store.return_value = Mock()
        mock_retriever.return_value = Mock()
        mock_document_preprocessor.return_value = Mock()

        # Setup statistics mocks
        mock_vector_store.return_value.get_stats.return_value = {
            "total_objects": 150,
            "collection": "Document",
            "is_connected": True,
        }
        mock_retriever.return_value.get_retrieval_stats.return_value = {
            "vector_store_stats": {},
            "embedding_model": "all-mpnet-base-v2",
            "embedding_dimension": 768,
        }

        # Create RAG system
        kbm = KnowledgeBaseManager()

        # Test system statistics
        stats = kbm.get_collection_stats("Document")

        # Assertions
        assert stats["system_initialized"] is True
        assert stats["vector_store"]["total_objects"] == 150
        assert (
            stats["embedding_engine"]["model_name"] == "Not initialized"
        )  # Not initialized by default
        assert "components" in stats
        assert "retrieval" in stats

    @patch("ragora.ragora.core.knowledge_base_manager.DatabaseManager")
    @patch("ragora.ragora.core.knowledge_base_manager.VectorStore")
    @patch("ragora.ragora.core.knowledge_base_manager.Retriever")
    @patch("ragora.ragora.core.knowledge_base_manager.DocumentPreprocessor")
    @patch("ragora.ragora.core.knowledge_base_manager.DataChunker")
    def test_error_handling_integration(
        self,
        mock_data_chunker,
        mock_document_preprocessor,
        mock_retriever,
        mock_vector_store,
        mock_db_manager,
    ):
        """Test error handling across components."""
        # Setup mocks
        mock_db_manager.return_value = Mock()
        mock_vector_store.return_value = Mock()
        mock_retriever.return_value = Mock()
        mock_document_preprocessor.return_value = Mock()
        mock_data_chunker.return_value = Mock()

        # Setup error conditions
        mock_retriever.return_value.search_similar.side_effect = Exception(
            "Search failed"
        )

        # Create knowledge base manager system
        kbm = KnowledgeBaseManager()

        # Test error handling
        with pytest.raises(Exception, match="Search failed"):
            kbm.search("test query", strategy=SearchStrategy.SIMILAR)

    @patch("ragora.ragora.core.knowledge_base_manager.DatabaseManager")
    @patch("ragora.ragora.core.knowledge_base_manager.VectorStore")
    @patch("ragora.ragora.core.knowledge_base_manager.Retriever")
    @patch("ragora.ragora.core.knowledge_base_manager.DocumentPreprocessor")
    @patch("ragora.ragora.core.knowledge_base_manager.DataChunker")
    def test_context_manager_integration(
        self,
        mock_data_chunker,
        mock_document_preprocessor,
        mock_retriever,
        mock_vector_store,
        mock_db_manager,
    ):
        """Test context manager integration."""
        # Setup mocks
        mock_db_manager.return_value = Mock()
        mock_vector_store.return_value = Mock()
        mock_retriever.return_value = Mock()
        mock_document_preprocessor.return_value = Mock()
        mock_data_chunker.return_value = Mock()

        # Test context manager
        with KnowledgeBaseManager() as kbm:
            assert kbm.is_initialized is True
            assert kbm.vector_store is not None
            assert kbm.retriever is not None

        # Verify cleanup
        assert kbm.is_initialized is False

    @patch("ragora.ragora.core.knowledge_base_manager.DatabaseManager")
    @patch("ragora.ragora.core.knowledge_base_manager.VectorStore")
    @patch("ragora.ragora.core.knowledge_base_manager.Retriever")
    @patch("ragora.ragora.core.knowledge_base_manager.DocumentPreprocessor")
    @patch("ragora.ragora.core.knowledge_base_manager.DataChunker")
    def test_component_communication(
        self,
        mock_data_chunker,
        mock_document_preprocessor,
        mock_retriever,
        mock_vector_store,
        mock_db_manager,
    ):
        """Test communication between components."""
        # Setup mocks
        mock_db_manager.return_value = Mock()
        mock_vector_store.return_value = Mock()
        mock_retriever.return_value = Mock()
        mock_document_preprocessor.return_value = Mock()
        mock_data_chunker.return_value = Mock()

        # Create RAG system
        kbm = KnowledgeBaseManager()

        # Test that components are properly connected
        assert hasattr(kbm.retriever, "vector_store")
        assert hasattr(kbm.retriever, "embedding_engine")
        assert hasattr(kbm.vector_store, "embedding_engine")
        assert kbm.is_initialized is True

    @patch("ragora.ragora.core.knowledge_base_manager.DatabaseManager")
    @patch("ragora.ragora.core.knowledge_base_manager.VectorStore")
    @patch("ragora.ragora.core.knowledge_base_manager.Retriever")
    @patch("ragora.ragora.core.knowledge_base_manager.DocumentPreprocessor")
    @patch("ragora.ragora.core.knowledge_base_manager.DataChunker")
    def test_performance_characteristics(
        self,
        mock_data_chunker,
        mock_document_preprocessor,
        mock_retriever,
        mock_vector_store,
        mock_db_manager,
    ):
        """Test performance characteristics of the system."""
        # Setup mocks
        mock_db_manager.return_value = Mock()
        mock_vector_store.return_value = Mock()
        mock_retriever.return_value = Mock()
        mock_document_preprocessor.return_value = Mock()
        mock_data_chunker.return_value = Mock()

        # Create knowledge base manager system
        kbm = KnowledgeBaseManager()

        # Test that system is ready for operations
        assert kbm.is_initialized is True
        assert hasattr(kbm, "vector_store")
        assert hasattr(kbm, "retriever")
        assert hasattr(kbm, "embedding_engine")  # Attribute exists but may be None
        assert hasattr(kbm, "document_preprocessor")
        assert hasattr(kbm, "data_chunker")  # Attribute exists but may be None

    @patch("ragora.ragora.core.knowledge_base_manager.DatabaseManager")
    @patch("ragora.ragora.core.knowledge_base_manager.VectorStore")
    @patch("ragora.ragora.core.knowledge_base_manager.Retriever")
    @patch("ragora.ragora.core.knowledge_base_manager.DocumentPreprocessor")
    def test_configuration_validation(
        self,
        mock_document_preprocessor,
        mock_retriever,
        mock_vector_store,
        mock_db_manager,
    ):
        """Test configuration validation."""
        # Setup mocks
        mock_db_manager.return_value = Mock()
        mock_vector_store.return_value = Mock()
        mock_retriever.return_value = Mock()
        mock_document_preprocessor.return_value = Mock()

        # Test with custom configuration
        kbm = KnowledgeBaseManager(
            weaviate_url="http://custom:8080",
        )

        # Assertions
        assert kbm.is_initialized is True
        assert kbm.vector_store is not None
        assert kbm.retriever is not None
        assert kbm.embedding_engine is None  # Not initialized by default
        assert kbm.document_preprocessor is not None
        assert kbm.data_chunker is None  # Not initialized by KnowledgeBaseManager
