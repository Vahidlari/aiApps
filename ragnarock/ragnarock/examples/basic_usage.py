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

from ragnarock import KnowledgeBaseManager

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
        kbm.vector_store.create_schema(force_recreate=True)

        # Example: Process a document (uncomment if you have a LaTeX file)
        # logger.info("📄 Processing LaTeX document...")
        # chunk_ids = kbm.process_document("path/to/your/document.tex")
        # logger.info(f"✅ Processed document, stored {len(chunk_ids)} chunks")

        # Example: Add some sample data for demonstration
        logger.info("📝 Adding sample data for demonstration...")
        from ragnarock import DataChunk

        sample_chunks = [
            DataChunk(
                text="The theory of relativity revolutionized our understanding of space and time.",
                start_idx=0,
                end_idx=80,
                metadata=None,
                chunk_id="demo_001",
                source_document="physics_demo.tex",
                chunk_type="text",
            ),
            DataChunk(
                text="E = mc² represents the mass-energy equivalence principle.",
                start_idx=81,
                end_idx=150,
                metadata=None,
                chunk_id="demo_002",
                source_document="physics_demo.tex",
                chunk_type="equation",
            ),
        ]

        # Store chunks
        stored_uuids = kbm.vector_store.store_chunks(sample_chunks)
        logger.info(f"✅ Stored {len(stored_uuids)} sample chunks")

        # Query the knowledge base
        logger.info("🔍 Querying the knowledge base...")
        response = kbm.query(
            "What is the relationship between mass and energy?",
            search_type="hybrid",
            top_k=3,
        )

        # Display results
        logger.info("📋 Query Results:")
        logger.info(f"   Question: {response['question']}")
        logger.info(f"   Retrieved {response['num_chunks']} chunks:")

        for i, chunk in enumerate(response["retrieved_chunks"], 1):
            logger.info(f"   {i}. {chunk['content'][:80]}...")

        # Get system statistics
        logger.info("📊 System Statistics:")
        stats = kbm.get_system_stats()
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
