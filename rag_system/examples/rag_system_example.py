#!/usr/bin/env python3
"""Example usage of the refactored RAG system.

This script demonstrates the new layered architecture with proper separation
of concerns between storage, retrieval, and orchestration layers.

Prerequisites:
- Weaviate running on localhost:8080
- Docker command: docker run -d --name weaviate -p 8080:8080 semitechnologies/weaviate:1.22.4
"""

import logging

from core.rag_system import RAGSystem

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main example function demonstrating the refactored RAG system."""
    try:
        # Initialize the RAG system (orchestrates all components)
        logger.info("Initializing RAG system...")
        rag = RAGSystem(
            weaviate_url="http://localhost:8080",
            class_name="ExampleDocument",
            embedding_model="all-mpnet-base-v2",
            chunk_size=768,
            chunk_overlap=100,
        )

        # Create schema
        logger.info("Creating vector store schema...")
        rag.vector_store.create_schema(force_recreate=True)

        # Example 1: Process a document (if you have a LaTeX file)
        # Uncomment the following lines if you have a LaTeX document to process
        # logger.info("Processing LaTeX document...")
        # chunk_ids = rag.process_document("path/to/your/document.tex")
        # logger.info(f"Processed document, stored {len(chunk_ids)} chunks")

        # Example 2: Direct storage using the new architecture
        logger.info("Demonstrating direct component usage...")

        # Use VectorStore directly for storage operations
        from core.data_chunker import DataChunk

        sample_chunks = [
            DataChunk(
                chunk_id="demo_001",
                text="The theory of relativity revolutionized our understanding of space and time.",
                source_document="physics_demo.tex",
                chunk_type="text",
                metadata={
                    "page_number": 1,
                    "section_title": "Introduction to Relativity",
                    "author": "Einstein",
                },
            ),
            DataChunk(
                chunk_id="demo_002",
                text="E = mc² represents the mass-energy equivalence principle.",
                source_document="physics_demo.tex",
                chunk_type="equation",
                metadata={
                    "page_number": 2,
                    "section_title": "Mass-Energy Equivalence",
                    "author": "Einstein",
                },
            ),
            DataChunk(
                chunk_id="demo_003",
                text="Quantum mechanics describes the behavior of matter at atomic scales.",
                source_document="physics_demo.tex",
                chunk_type="text",
                metadata={
                    "page_number": 3,
                    "section_title": "Quantum Mechanics",
                    "author": "Planck",
                },
            ),
        ]

        # Store chunks using VectorStore
        logger.info("Storing sample chunks...")
        stored_uuids = rag.vector_store.store_chunks(sample_chunks)
        logger.info(f"Stored {len(stored_uuids)} chunks with UUIDs: {stored_uuids}")

        # Example 3: Use Retriever for search operations
        logger.info("Demonstrating retrieval operations...")

        # Vector similarity search
        logger.info("Performing vector similarity search...")
        similar_results = rag.retriever.search_similar(
            "What is the relationship between mass and energy?", top_k=3
        )

        logger.info(f"Found {len(similar_results)} similar results:")
        for i, result in enumerate(similar_results, 1):
            logger.info(f"  {i}. Score: {result['similarity_score']:.3f}")
            logger.info(f"     Content: {result['content'][:80]}...")
            logger.info(f"     Type: {result['chunk_type']}")
            logger.info("")

        # Hybrid search
        logger.info("Performing hybrid search...")
        hybrid_results = rag.retriever.search_hybrid(
            "Einstein physics equations", alpha=0.7, top_k=3
        )

        logger.info(f"Found {len(hybrid_results)} hybrid results:")
        for i, result in enumerate(hybrid_results, 1):
            logger.info(f"  {i}. Score: {result['hybrid_score']:.3f}")
            logger.info(f"     Content: {result['content'][:80]}...")
            logger.info("")

        # Citation search
        logger.info("Performing citation search...")
        citation_results = rag.retriever.search_citations(author="Einstein", top_k=5)

        logger.info(f"Found {len(citation_results)} citation results:")
        for i, result in enumerate(citation_results, 1):
            logger.info(f"  {i}. Author: {result['metadata'].get('author', 'Unknown')}")
            logger.info(f"     Content: {result['content'][:80]}...")
            logger.info("")

        # Equation search
        logger.info("Performing equation search...")
        equation_results = rag.retriever.search_equations(
            "mass energy equivalence", top_k=3
        )

        logger.info(f"Found {len(equation_results)} equation results:")
        for i, result in enumerate(equation_results, 1):
            logger.info(f"  {i}. Type: {result['chunk_type']}")
            logger.info(f"     Content: {result['content'][:80]}...")
            logger.info("")

        # Example 4: Use RAGSystem for unified queries
        logger.info("Demonstrating unified RAG queries...")

        # Unified query interface
        query_response = rag.query(
            "What did Einstein discover about mass and energy?",
            search_type="hybrid",
            top_k=3,
        )

        logger.info("Unified query response:")
        logger.info(f"  Question: {query_response['question']}")
        logger.info(f"  Search type: {query_response['search_type']}")
        logger.info(f"  Retrieved chunks: {query_response['num_chunks']}")
        logger.info(f"  Sources: {query_response['chunk_sources']}")
        logger.info(f"  Chunk types: {query_response['chunk_types']}")
        if "avg_similarity" in query_response:
            logger.info(f"  Average similarity: {query_response['avg_similarity']:.3f}")
        logger.info("")

        # Example 5: System statistics
        logger.info("Getting system statistics...")
        stats = rag.get_system_stats()

        logger.info("System Statistics:")
        logger.info(f"  Initialized: {stats['system_initialized']}")
        logger.info(f"  Total objects: {stats['vector_store']['total_objects']}")
        logger.info(f"  Embedding model: {stats['embedding_engine']['model_name']}")
        logger.info(f"  Chunk size: {stats['data_chunker']['chunk_size']}")
        logger.info(f"  Components: {stats['components']}")
        logger.info("")

        # Example 6: Individual component access
        logger.info("Demonstrating individual component access...")

        # Access specific chunk
        chunk_data = rag.get_chunk("demo_002")
        if chunk_data:
            logger.info(f"Retrieved chunk demo_002:")
            logger.info(f"  Content: {chunk_data['content']}")
            logger.info(f"  Metadata: {chunk_data['metadata']}")
        logger.info("")

        # Example 7: Cleanup
        logger.info("Demonstrating cleanup operations...")

        # Delete a specific chunk
        deleted = rag.delete_chunk("demo_003")
        if deleted:
            logger.info("Successfully deleted chunk demo_003")
        else:
            logger.info("Failed to delete chunk demo_003")

        # Get updated statistics
        updated_stats = rag.get_system_stats()
        logger.info(
            f"Updated total objects: {updated_stats['vector_store']['total_objects']}"
        )

        logger.info("Example completed successfully!")
        logger.info("")
        logger.info("Architecture Summary:")
        logger.info("  ✅ VectorStore: Handles storage operations only")
        logger.info("  ✅ Retriever: Handles search and retrieval logic")
        logger.info("  ✅ RAGSystem: Orchestrates all components")
        logger.info("  ✅ Clean separation of concerns achieved!")

    except Exception as e:
        logger.error(f"Error in example: {str(e)}")
        raise
    finally:
        # Close the RAG system
        if "rag" in locals():
            rag.close()


if __name__ == "__main__":
    main()
