"""
Pytest configuration and shared fixtures for RAG system tests.
"""

import tempfile
from pathlib import Path

import pytest

from ragora.utils.latex_parser import Citation, LatexDocument, LatexParser


@pytest.fixture
def sample_latex_content():
    """Sample LaTeX content for testing."""
    return r"""
\documentclass{article}
\title{Sample Document}
\author{Test Author}
\date{2024}

\begin{document}
\maketitle

\section{Introduction}
This is a sample paragraph with a citation \cite{einstein1905}.

\subsection{Methodology}
Here's another paragraph with multiple citations \cite{einstein1905,newton1687}.

\section{Results}
\begin{table}[h]
\centering
\caption{Sample Table}
\label{tab:sample}
\begin{tabular}{|c|c|}
\hline
Column 1 & Column 2 \\
\hline
Value 1 & Value 2 \\
\hline
\end{tabular}
\end{table}

\begin{figure}[h]
\centering
\caption{Sample Figure}
\label{fig:sample}
\end{figure}

\end{document}
"""


@pytest.fixture
def sample_bibliography_content():
    """Sample bibliography content for testing."""
    return r"""
@article{einstein1905,
    author = {Einstein, Albert},
    title = {On the Electrodynamics of Moving Bodies},
    journal = {Annalen der Physik},
    year = {1905},
    doi = {10.1002/andp.19053221004}
}

@book{newton1687,
    author = {Newton, Isaac},
    title = {Philosophiæ Naturalis Principia Mathematica},
    year = {1687},
    publisher = {Royal Society}
}
"""


@pytest.fixture
def temp_latex_file(sample_latex_content):
    """Create a temporary LaTeX file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", delete=False) as f:
        f.write(sample_latex_content)
        f.flush()
        yield Path(f.name)

    # Cleanup
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def temp_bibliography_file(sample_bibliography_content):
    """Create a temporary bibliography file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".bib", delete=False) as f:
        f.write(sample_bibliography_content)
        f.flush()
        yield Path(f.name)

    # Cleanup
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def latex_parser():
    """Create a LatexParser instance for testing."""
    return LatexParser()


@pytest.fixture
def sample_citation():
    """Create a sample Citation object for testing."""
    return Citation(
        author="Einstein, Albert",
        year="1905",
        title="On the Electrodynamics of Moving Bodies",
        doi="10.1002/andp.19053221004",
        source_document="test.tex",
        page_reference="17",
        citation_label="einstein1905",
        citation_hash=hash("einstein1905"),
    )


@pytest.fixture
def sample_latex_document():
    """Create a sample LatexDocument object for testing."""
    return LatexDocument(
        title="Sample Document",
        author="Test Author",
        year="2024",
        doi="",
        source_document="test.tex",
        page_reference="1",
    )


@pytest.fixture
def complex_latex_content():
    """Complex LaTeX content with multiple structures for testing."""
    return r"""
\documentclass{book}
\title{Complex Scientific Document}
\author{Dr. Jane Smith}
\date{2024}

\begin{document}
\maketitle

This document has multiple chapters, sections, subsections, and paragraphs.

\chapter{Introduction}
\label{ch:intro}

This chapter introduces the main concepts. We reference \cite{smith2023} and \citep{jones2022}.

\section{Background}
\label{sec:background}

The background section contains important information \citet{doe2021}.

\subsection{Related Work}
\label{subsec:related}

Previous work has shown \cite{smith2023,jones2022,doe2021}.

\section{Methodology}
\label{sec:method}

Our approach is described in Table~\ref{tab:results}.

\begin{table}[h]
\centering
\caption{Experimental Results}
\label{tab:results}
\begin{tabular}{|l|c|c|}
\hline
Method & Accuracy & Time (s) \\
\hline
Baseline & 0.85 & 10.2 \\
Proposed & 0.92 & 8.7 \\
\hline
\end{tabular}
\end{table}

Figure~\ref{fig:architecture} shows our system architecture.

\begin{figure}[h]
\centering
\caption{System Architecture}
\label{fig:architecture}
\end{figure}

\chapter{Results}
\label{ch:results}

The results are presented in the following sections.

\section{Performance Analysis}
\label{sec:performance}

Our system achieves state-of-the-art performance.

\end{document}
"""


@pytest.fixture
def malformed_latex_content():
    """Malformed LaTeX content for error handling tests."""
    return r"""
\documentclass{article}
\title{Malformed Document}

\begin{document}
\section{Unclosed Section
This paragraph has unclosed braces { and missing citations \cite{.

\begin{table}
\caption{Incomplete table
\begin{tabular}{|c|c|}
\hline
Missing closing
\end{document}
"""


@pytest.fixture
def temp_complex_latex_file(complex_latex_content):
    """Create a temporary LaTeX file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", delete=False) as f:
        f.write(complex_latex_content)
        f.flush()
        yield Path(f.name)

    # Cleanup
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def config_dict():
    """Sample configuration dictionary for testing."""
    return {
        "chunk": {
            "chunk_size": 768,
            "overlap_size": 100,
            "chunk_type": "text",
        },
        "embedding": {
            "model_name": "all-mpnet-base-v2",
            "max_length": 512,
            "device": None,
        },
        "database_manager": {
            "url": "http://localhost:8080",
            "grpc_port": 50051,
            "timeout": 30,
            "retry_attempts": 3,
        },
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
