#!/usr/bin/env python3
"""Basic usage example for the knowledge base manager package.

This example demonstrates the simplest way to use the knowledge base manager:
1. Import the KnowledgeBaseManager class
2. Initialize with default settings
3. Process a document
4. Query the knowledge base

Prerequisites:
- Weaviate running on localhost:8080
- Docker command: docker run -d --name weaviate -p 8080:8080 semitechnologies/weaviate:1.22.4
"""

import logging

from ragora import FilterBuilder, KnowledgeBaseManager, SearchStrategy

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Basic usage example."""
    try:
        # Initialize the knowledge base manager with default settings
        logger.info("🚀 Initializing knowledge base manager...")
        kbm = KnowledgeBaseManager()

        # Create schema
        logger.info("📊 Creating vector store schema...")
        kbm.vector_store.create_schema("Document", force_recreate=True)

        # Example: Process a document (uncomment if you have a LaTeX file)
        # logger.info("📄 Processing LaTeX document...")
        # chunk_ids = kbm.process_document("path/to/your/document.tex")
        # logger.info(f"✅ Processed document, stored {len(chunk_ids)} chunks")

        # Example: Add some sample data for demonstration
        logger.info("📝 Adding sample data for demonstration...")
        from ragora import ChunkMetadata, DataChunk

        sample_chunks = [
            DataChunk(
                text="The theory of relativity revolutionized our understanding of space and time.",
                start_idx=0,
                end_idx=80,
                metadata=ChunkMetadata(
                    chunk_idx=1,
                    chunk_size=80,
                    total_chunks=2,
                    source_document="physics_demo.tex",
                    page_number=1,
                    section_title="Introduction",
                    chunk_type="text",
                    created_at="2024-01-15T10:00:00Z",
                    custom_metadata={
                        "language": "en",
                        "domain": "scientific",
                        "confidence": 0.95,
                        "tags": ["physics", "relativity"],
                        "priority": 5,
                        "content_category": "research",
                    },
                ),
                chunk_id="demo_001",
                source_document="physics_demo.tex",
                chunk_type="text",
            ),
            DataChunk(
                text="E = mc² represents the mass-energy equivalence principle.",
                start_idx=81,
                end_idx=150,
                metadata=ChunkMetadata(
                    chunk_idx=2,
                    chunk_size=69,
                    total_chunks=2,
                    source_document="physics_demo.tex",
                    page_number=1,
                    section_title="Mathematical Content",
                    chunk_type="equation",
                    created_at="2024-01-15T10:00:00Z",
                    custom_metadata={
                        "language": "en",
                        "domain": "scientific",
                        "confidence": 0.98,
                        "tags": ["physics", "equation", "einstein"],
                        "priority": 5,
                        "content_category": "mathematical_formula",
                    },
                ),
                chunk_id="demo_002",
                source_document="physics_demo.tex",
                chunk_type="equation",
            ),
        ]

        # Store chunks
        stored_uuids = kbm.vector_store.store_chunks(sample_chunks, "Document")
        logger.info(f"✅ Stored {len(stored_uuids)} sample chunks with custom metadata")

        # Query the knowledge base
        logger.info("🔍 Querying the knowledge base...")
        response = kbm.search(
            "What is the relationship between mass and energy?",
            strategy=SearchStrategy.HYBRID,
            top_k=3,
        )

        # Example: Query with filter (only text chunks)
        logger.info("🔍 Querying with filter (text chunks only)...")
        text_filter = FilterBuilder.by_chunk_type("text")
        filtered_response = kbm.search(
            "What is the relationship between mass and energy?",
            strategy=SearchStrategy.HYBRID,
            top_k=3,
            filter=text_filter,
        )
        logger.info(
            f"   Filtered results: {filtered_response.total_found} chunks (text type only)"
        )

        # Display results
        logger.info("📋 Search Results:")
        logger.info(f"   Query: {response.query}")
        logger.info(f"   Strategy: {response.strategy.value}")
        logger.info(f"   Retrieved {response.total_found} chunks:")
        logger.info(f"   Execution time: {response.execution_time:.3f}s")

        for i, chunk in enumerate(response.results, 1):
            logger.info(f"   {i}. {chunk['content'][:80]}...")
            # Show custom metadata if available
            if chunk.get("metadata", {}).get("language"):
                logger.info(
                    f"      Language: {chunk['metadata']['language']}, Domain: {chunk['metadata']['domain']}"
                )

        # Get system statistics
        logger.info("📊 System Statistics:")
        stats = kbm.get_collection_stats("Document")
        logger.info(f"   Total objects: {stats['vector_store']['total_objects']}")
        logger.info(f"   Embedding model: {stats['embedding_engine']['model_name']}")

        logger.info("✅ Basic usage example completed successfully!")

    except Exception as e:
        logger.error(f"❌ Error in basic usage example: {str(e)}")
        raise
    finally:
        # Clean up
        if "kbm" in locals():
            kbm.close()


if __name__ == "__main__":
    main()
