"""
Sample queries and usage examples for the LaTeX RAG System.

This file demonstrates how to use the RAG system with different types of queries
and shows the expected outputs.
"""

from rag_system.config import ChunkConfig
from rag_system.core import RAGSystem


def setup_rag_system():
    """Initialize the RAG system with default configuration."""
    config = ChunkConfig(
        chunk_size=768,
        overlap=100,
        preserve_equations=True,
        remove_latex_commands=True,
        separate_citations=True,
    )
    return RAGSystem(config)


def example_queries():
    """Example queries demonstrating different use cases."""

    # Initialize the system
    rag = setup_rag_system()

    # Example 1: Factual question about equations
    print("=== Example 1: Equation Query ===")
    query = "What is the main equation in chapter 2?"
    response = rag.query(query)
    print(f"Query: {query}")
    print(f"Response: {response}")
    print()

    # Example 2: Conceptual question
    print("=== Example 2: Conceptual Query ===")
    query = "How does the author explain quantum mechanics?"
    response = rag.query(query)
    print(f"Query: {query}")
    print(f"Response: {response}")
    print()

    # Example 3: Citation-specific query
    print("=== Example 3: Citation Query ===")
    query = "What does Einstein (1905) say about relativity?"
    response = rag.query(query)
    print(f"Query: {query}")
    print(f"Response: {response}")
    print()

    # Example 4: Comparative question
    print("=== Example 4: Comparative Query ===")
    query = "Compare the approaches in sections 3.1 and 3.2"
    response = rag.query(query)
    print(f"Query: {query}")
    print(f"Response: {response}")
    print()

    # Example 5: Technical term query
    print("=== Example 5: Technical Term Query ===")
    query = "What is the definition of entropy?"
    response = rag.query(query)
    print(f"Query: {query}")
    print(f"Response: {response}")
    print()


def batch_processing_example():
    """Example of processing multiple documents at once."""

    rag = setup_rag_system()

    # List of LaTeX files to process
    latex_files = [
        "examples/latex_samples/chapter_1.tex",
        "examples/latex_samples/chapter_2.tex",
        "examples/latex_samples/appendix.tex",
    ]

    print("=== Batch Processing Example ===")

    # Process all documents
    for file_path in latex_files:
        try:
            rag.process_document(file_path)
            print(f"✓ Processed: {file_path}")
        except Exception as e:
            print(f"✗ Failed to process {file_path}: {e}")

    print("Batch processing completed!")
    print()


def citation_queries_example():
    """Example queries specifically for citation handling."""

    rag = setup_rag_system()

    print("=== Citation Queries Example ===")

    # Query by author
    query = "What research has been done by Feynman?"
    response = rag.query(query)
    print(f"Query: {query}")
    print(f"Response: {response}")
    print()

    # Query by year
    query = "What papers were published in 1927?"
    response = rag.query(query)
    print(f"Query: {query}")
    print(f"Response: {response}")
    print()

    # Query by specific citation
    query = "What does the paper 'On the Electrodynamics of Moving Bodies' discuss?"
    response = rag.query(query)
    print(f"Query: {query}")
    print(f"Response: {response}")
    print()


def equation_queries_example():
    """Example queries for mathematical content."""

    rag = setup_rag_system()

    print("=== Equation Queries Example ===")

    # Query about specific equation
    query = "What is the Schrödinger equation?"
    response = rag.query(query)
    print(f"Query: {query}")
    print(f"Response: {response}")
    print()

    # Query about mathematical concept
    query = "How is the Fourier transform defined?"
    response = rag.query(query)
    print(f"Query: {query}")
    print(f"Response: {response}")
    print()

    # Query about equation applications
    query = "What are the applications of Maxwell's equations?"
    response = rag.query(query)
    print(f"Query: {query}")
    print(f"Response: {response}")
    print()


def performance_testing():
    """Example of testing system performance."""

    rag = setup_rag_system()

    print("=== Performance Testing ===")

    import time

    # Test query response time
    query = "What is the main topic of the book?"

    start_time = time.time()
    response = rag.query(query)
    end_time = time.time()

    response_time = end_time - start_time
    print(f"Query response time: {response_time:.2f} seconds")
    print(f"Response: {response}")
    print()


if __name__ == "__main__":
    """Run all example queries."""

    print("LaTeX RAG System - Sample Queries")
    print("=" * 50)
    print()

    # Run examples
    example_queries()
    batch_processing_example()
    citation_queries_example()
    equation_queries_example()
    performance_testing()

    print("All examples completed!")
