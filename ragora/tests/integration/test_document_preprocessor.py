"""
Integration tests for DocumentPreprocessor in the RAG system.

These tests verify the complete preprocessing pipeline with real files,
including parsing, text extraction, and chunking.
"""

import os
import tempfile

import pytest

from ragora import (
    ChunkingContext,
    ChunkingContextBuilder,
    ChunkMetadata,
    DataChunk,
    DataChunker,
    DocumentPreprocessor,
)


class TestDocumentPreprocessorIntegration:
    """Integration tests for DocumentPreprocessor."""

    @pytest.fixture
    def sample_latex_content(self):
        """Sample LaTeX content for testing."""
        return r"""
\documentclass{article}
\usepackage{amsmath}
\usepackage{amsfonts}

\title{Sample Scientific Document}
\author{Dr. John Doe}
\date{2024}

\begin{document}
\maketitle

\section{Introduction}
This is the introduction section. It contains some basic information about
the topic.

\subsection{Background}
This subsection provides background information. It includes some
mathematical content: $E = mc^2$.

\section{Methodology}
This section describes the methodology used in the research.

\subsection{Data Collection}
We collected data from various sources. The data is presented in
Table~\ref{tab:sample}.

\begin{table}[h]
\centering
\caption{Sample Data Table}
\label{tab:sample}
\begin{tabular}{|c|c|}
\hline
Parameter & Value \\
\hline
A & 1.0 \\
B & 2.0 \\
C & 3.0 \\
\hline
\end{tabular}
\end{table}

\section{Results}
The results show significant improvements in performance.

\subsection{Analysis}
Our analysis reveals several key findings:
\begin{itemize}
\item First finding
\item Second finding
\item Third finding
\end{itemize}

\section{Conclusion}
In conclusion, we have demonstrated the effectiveness of our approach.

\end{document}
"""

    @pytest.fixture
    def complex_latex_content(self):
        """Complex LaTeX content with multiple chapters."""
        return r"""
\documentclass{book}
\usepackage{amsmath}
\usepackage{amsfonts}

\title{Complex Scientific Document}
\author{Dr. Jane Smith}
\date{2024}

\begin{document}
\maketitle

\chapter{Introduction}
This chapter introduces the main concepts.

\section{Problem Statement}
The problem we address is complex and multifaceted.

\subsection{Research Questions}
Our research addresses the following questions:
\begin{enumerate}
\item What is the optimal approach?
\item How can we measure success?
\item What are the limitations?
\end{enumerate}

\chapter{Literature Review}
This chapter reviews relevant literature.

\section{Previous Work}
Previous work has shown various approaches to this problem.

\subsection{Method A}
Method A was proposed by Smith et al. in 2020.

\subsection{Method B}
Method B was developed by Johnson and Brown in 2021.

\chapter{Methodology}
This chapter describes our methodology.

\section{Experimental Setup}
We conducted experiments using the following setup.

\begin{table}[h]
\centering
\caption{Experimental Parameters}
\label{tab:params}
\begin{tabular}{|l|c|}
\hline
Parameter & Value \\
\hline
Learning Rate & 0.001 \\
Batch Size & 32 \\
Epochs & 100 \\
\hline
\end{tabular}
\end{table}

\section{Data Preprocessing}
Data preprocessing involved several steps.

\chapter{Results}
This chapter presents our results.

\section{Quantitative Results}
The quantitative results are shown in Table~\ref{tab:results}.

\begin{table}[h]
\centering
\caption{Experimental Results}
\label{tab:results}
\begin{tabular}{|l|c|c|}
\hline
Method & Accuracy & F1-Score \\
\hline
Baseline & 0.75 & 0.72 \\
Our Method & 0.89 & 0.87 \\
\hline
\end{tabular}
\end{table}

\section{Qualitative Analysis}
Our qualitative analysis reveals several insights.

\chapter{Conclusion}
We conclude with a summary of our findings.

\end{document}
"""

    @pytest.fixture
    def minimal_latex_content(self):
        """Minimal LaTeX content for testing."""
        return r"""
\documentclass{article}
\title{Minimal Document}
\author{Test Author}
\date{2024}
\begin{document}
\maketitle
\section{Simple Section}
This is a simple section with minimal content.
\end{document}
"""

    def test_preprocess_single_document_integration(self, sample_latex_content):
        """Test preprocessing a single document with real file."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", delete=False) as f:
            f.write(sample_latex_content)
            f.flush()
            file_path = f.name

        try:
            # Create preprocessor
            preprocessor = DocumentPreprocessor()

            # Process document
            chunks = preprocessor.preprocess_document(file_path)

            # Verify results
            assert isinstance(chunks, list)
            assert len(chunks) > 0

            # Check chunk structure
            for chunk in chunks:
                assert isinstance(chunk, DataChunk)
                assert isinstance(chunk.text, str)
                assert len(chunk.text) > 0
                assert isinstance(chunk.start_idx, int)
                assert isinstance(chunk.end_idx, int)
                assert isinstance(chunk.metadata, ChunkMetadata)

            # Verify content is extracted
            all_text = " ".join(chunk.text for chunk in chunks)
            assert "Introduction" in all_text
            assert "Methodology" in all_text
            assert "Results" in all_text
            assert "Conclusion" in all_text

        finally:
            # Clean up
            os.unlink(file_path)

    def test_preprocess_multiple_documents_integration(
        self, sample_latex_content, minimal_latex_content
    ):
        """Test preprocessing multiple documents."""
        # Create temporary files
        file_paths = []
        try:
            for i, content in enumerate([sample_latex_content, minimal_latex_content]):
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=f"_{i}.tex", delete=False
                ) as f:
                    f.write(content)
                    f.flush()
                    file_paths.append(f.name)

            # Create preprocessor
            preprocessor = DocumentPreprocessor()

            # Process documents
            chunks = preprocessor.preprocess_documents(file_paths)

            # Verify results
            assert isinstance(chunks, list)
            assert len(chunks) > 0

            # Verify content from both documents
            all_text = " ".join(chunk.text for chunk in chunks)
            assert "Introduction" in all_text
            assert "Simple Section" in all_text

        finally:
            # Clean up
            for file_path in file_paths:
                os.unlink(file_path)

    def test_preprocess_document_folder_integration(
        self, sample_latex_content, minimal_latex_content
    ):
        """Test preprocessing documents from a folder."""
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files in the directory
            file_paths = []
            for i, content in enumerate([sample_latex_content, minimal_latex_content]):
                file_path = os.path.join(temp_dir, f"document_{i}.tex")
                with open(file_path, "w") as f:
                    f.write(content)
                file_paths.append(file_path)

            # Create preprocessor
            preprocessor = DocumentPreprocessor()

            # Process folder
            chunks = preprocessor.preprocess_document_folder(temp_dir)

            # Verify results
            assert isinstance(chunks, list)
            assert len(chunks) > 0

            # Verify content from both documents
            all_text = " ".join(chunk.text for chunk in chunks)
            assert "Introduction" in all_text
            assert "Simple Section" in all_text

    def test_preprocess_complex_document_integration(self, complex_latex_content):
        """Test preprocessing a complex document with chapters."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", delete=False) as f:
            f.write(complex_latex_content)
            f.flush()
            file_path = f.name

        try:
            # Create preprocessor
            preprocessor = DocumentPreprocessor()

            # Process document
            chunks = preprocessor.preprocess_document(file_path)

            # Verify results
            assert isinstance(chunks, list)
            assert len(chunks) > 0

            # Verify content structure
            all_text = " ".join(chunk.text for chunk in chunks)
            assert "Introduction" in all_text
            assert "Literature Review" in all_text
            assert "Methodology" in all_text
            assert "Results" in all_text
            assert "Conclusion" in all_text

            # Check for chapter and section headers
            assert "# Introduction" in all_text
            assert "# Literature Review" in all_text
            assert "## Problem Statement" in all_text
            assert "## Previous Work" in all_text

        finally:
            # Clean up
            os.unlink(file_path)

    def test_chunking_integration_with_custom_parameters(self, sample_latex_content):
        """Test integration with custom chunking parameters."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", delete=False) as f:
            f.write(sample_latex_content)
            f.flush()
            file_path = f.name

        try:
            # Create custom chunker with custom strategy
            from ragora import TextChunkingStrategy

            custom_strategy = TextChunkingStrategy(chunk_size=512, overlap_size=50)
            custom_chunker = DataChunker(default_strategy=custom_strategy)

            # Create preprocessor with custom chunker
            preprocessor = DocumentPreprocessor(chunker=custom_chunker)

            # Process document
            chunks = preprocessor.preprocess_document(file_path)

            # Verify results
            assert isinstance(chunks, list)
            assert len(chunks) > 0

            # Verify chunker parameters
            assert preprocessor.chunker.default_strategy.chunk_size == 512
            assert preprocessor.chunker.default_strategy.overlap_size == 50

        finally:
            # Clean up
            os.unlink(file_path)

    def test_table_extraction_integration(self, sample_latex_content):
        """Test table extraction and formatting."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", delete=False) as f:
            f.write(sample_latex_content)
            f.flush()
            file_path = f.name

        try:
            # Create preprocessor
            preprocessor = DocumentPreprocessor()

            # Process document
            chunks = preprocessor.preprocess_document(file_path)

            # Verify table content is extracted
            all_text = " ".join(chunk.text for chunk in chunks)
            assert "Table: Sample Data Table" in all_text
            assert "Parameter" in all_text
            assert "Value" in all_text
            assert "A" in all_text
            assert "1.0" in all_text

        finally:
            # Clean up
            os.unlink(file_path)

    def test_mathematical_content_handling(self, sample_latex_content):
        """Test handling of mathematical content."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", delete=False) as f:
            f.write(sample_latex_content)
            f.flush()
            file_path = f.name

        try:
            # Create preprocessor
            preprocessor = DocumentPreprocessor()

            # Process document
            chunks = preprocessor.preprocess_document(file_path)

            # Verify mathematical content is handled
            all_text = " ".join(chunk.text for chunk in chunks)
            # Mathematical content should be processed
            # (exact format depends on parser)
            assert "mathematical content" in all_text.lower()

        finally:
            # Clean up
            os.unlink(file_path)

    def test_error_handling_invalid_file(self):
        """Test error handling with invalid file."""
        # Create preprocessor
        preprocessor = DocumentPreprocessor()

        # Test with non-existent file
        with pytest.raises(ValueError, match="Document cannot be None"):
            preprocessor.preprocess_document("nonexistent_file.tex")

    def test_error_handling_invalid_folder(self):
        """Test error handling with invalid folder."""
        # Create preprocessor
        preprocessor = DocumentPreprocessor()

        # Test with non-existent folder
        with pytest.raises(FileNotFoundError):
            preprocessor.preprocess_document_folder("/nonexistent/folder")

    def test_error_handling_malformed_latex(self):
        """Test error handling with malformed LaTeX."""
        malformed_content = r"""
\documentclass{article}
\begin{document}
\section{Test}
This is a test section.
% Missing \end{document}
"""

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", delete=False) as f:
            f.write(malformed_content)
            f.flush()
            file_path = f.name

        try:
            # Create preprocessor
            preprocessor = DocumentPreprocessor()

            # Process document - should handle gracefully
            chunks = preprocessor.preprocess_document(file_path)

            # Should still produce some chunks even with malformed content
            assert isinstance(chunks, list)

        finally:
            # Clean up
            os.unlink(file_path)

    def test_empty_document_handling(self):
        """Test handling of empty document."""
        empty_content = r"""
\documentclass{article}
\begin{document}
\end{document}
"""

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", delete=False) as f:
            f.write(empty_content)
            f.flush()
            file_path = f.name

        try:
            # Create preprocessor
            preprocessor = DocumentPreprocessor()

            # Process document
            chunks = preprocessor.preprocess_document(file_path)

            # Should handle empty document gracefully
            assert isinstance(chunks, list)
            # May be empty or contain minimal chunks

        finally:
            # Clean up
            os.unlink(file_path)

    def test_large_document_performance(self):
        """Test performance with a larger document."""
        # Create a larger document
        large_content = r"""
\documentclass{article}
\title{Large Test Document}
\author{Test Author}
\begin{document}
\maketitle
"""

        # Add many sections
        for i in range(50):
            large_content += f"""
\\section{{Section {i}}}
This is section {i} with some content. It contains multiple paragraphs
and various elements to test the performance of the document preprocessor.

\\subsection{{Subsection {i}.1}}
This is subsection {i}.1 with additional content.

\\subsection{{Subsection {i}.2}}
This is subsection {i}.2 with more content.
"""

        large_content += r"""
\end{document}
"""

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", delete=False) as f:
            f.write(large_content)
            f.flush()
            file_path = f.name

        try:
            # Create preprocessor
            preprocessor = DocumentPreprocessor()

            # Process document
            chunks = preprocessor.preprocess_document(file_path)

            # Verify results
            assert isinstance(chunks, list)
            assert len(chunks) > 0

            # Verify content
            all_text = " ".join(chunk.text for chunk in chunks)
            assert "Section 0" in all_text
            assert "Section 49" in all_text

        finally:
            # Clean up
            os.unlink(file_path)

    def test_mixed_content_types_integration(self):
        """Test processing document with mixed content types."""
        mixed_content = r"""
\documentclass{article}
\title{Mixed Content Document}
\author{Test Author}
\begin{document}
\maketitle

\section{Text Section}
This section contains regular text content.

\subsection{List Subsection}
This subsection contains a list:
\begin{itemize}
\item First item
\item Second item
\item Third item
\end{itemize}

\section{Table Section}
This section contains a table:

\begin{table}[h]
\centering
\caption{Mixed Content Table}
\begin{tabular}{|l|c|}
\hline
Type & Count \\
\hline
Text & 100 \\
Tables & 5 \\
Lists & 10 \\
\hline
\end{tabular}
\end{table}

\section{Math Section}
This section contains mathematical content: $x = y + z$.

\subsection{Equation Subsection}
Here's an equation:
\begin{equation}
E = mc^2
\end{equation}

\end{document}
"""

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", delete=False) as f:
            f.write(mixed_content)
            f.flush()
            file_path = f.name

        try:
            # Create preprocessor
            preprocessor = DocumentPreprocessor()

            # Process document
            chunks = preprocessor.preprocess_document(file_path)

            # Verify results
            assert isinstance(chunks, list)
            assert len(chunks) > 0

            # Verify different content types are processed
            all_text = " ".join(chunk.text for chunk in chunks)
            assert "Text Section" in all_text
            assert "Table Section" in all_text
            assert "Math Section" in all_text
            assert "Table: Mixed Content Table" in all_text
            assert "Type" in all_text
            assert "Count" in all_text

        finally:
            # Clean up
            os.unlink(file_path)

    def test_metadata_preservation(self, sample_latex_content):
        """Test that document metadata is preserved in chunks."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", delete=False) as f:
            f.write(sample_latex_content)
            f.flush()
            file_path = f.name

        try:
            # Create preprocessor
            preprocessor = DocumentPreprocessor()

            # Process document
            chunks = preprocessor.preprocess_document(file_path)

            # Verify metadata is present
            for chunk in chunks:
                assert isinstance(chunk.metadata, ChunkMetadata)
                # Metadata structure depends on implementation
                # but should be present

        finally:
            # Clean up
            os.unlink(file_path)

    def test_chunk_overlap_verification(self, complex_latex_content):
        """Test that chunk overlap is working correctly."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", delete=False) as f:
            f.write(complex_latex_content)
            f.flush()
            file_path = f.name

        try:
            # Create preprocessor with specific overlap using custom strategy
            from ragora import TextChunkingStrategy

            custom_strategy = TextChunkingStrategy(chunk_size=200, overlap_size=50)
            custom_chunker = DataChunker(default_strategy=custom_strategy)
            preprocessor = DocumentPreprocessor(chunker=custom_chunker)

            # Process document
            chunks = preprocessor.preprocess_document(file_path)

            # Verify chunks have proper structure
            assert len(chunks) > 1  # Should have multiple chunks for overlap

            # Check that chunks have proper indices
            for i, chunk in enumerate(chunks):
                assert chunk.start_idx >= 0
                assert chunk.end_idx > chunk.start_idx
                if i > 0:
                    # Check for overlap (end of previous chunk should be >
                    # start of current)
                    assert chunks[i - 1].end_idx > chunk.start_idx

        finally:
            # Clean up
            os.unlink(file_path)
