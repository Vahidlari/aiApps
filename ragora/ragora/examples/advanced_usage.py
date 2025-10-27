#!/usr/bin/env python3
"""Advanced usage example for the knowledge base manager package.

This example demonstrates advanced usage with custom configuration:
1. Custom configuration setup
2. Multiple document processing
3. Different search types
4. System monitoring and statistics

Prerequisites:
- Weaviate running on localhost:8080 (or set WEAVIATE_URL in .env file)
- Docker command: docker run -d --name weaviate -p 8080:8080 \
  semitechnologies/weaviate:1.22.4

Environment Variables (.env file):
- WEAVIATE_URL: Weaviate server URL (defaults to http://localhost:8080)
"""

import logging
import os
from datetime import datetime

from dotenv import load_dotenv

from ragora import (
    ChunkConfig,
    DatabaseManagerConfig,
    DataChunk,
    EmbeddingConfig,
    KnowledgeBaseManager,
    KnowledgeBaseManagerConfig,
)
from ragora.core.chunking import ChunkMetadata

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_weaviate_url_from_file():
    """Get Weaviate URL from a .env file."""
    # load the .env file
    load_dotenv()
    # get the weaviate_url from the .env file
    weaviate_url = os.getenv("WEAVIATE_URL")
    return weaviate_url


def main():
    """Advanced usage example."""
    try:
        # Get Weaviate URL from .env file or use default
        weaviate_url = get_weaviate_url_from_file() or "http://localhost:8080"
        logger.info(f"Using Weaviate URL: {weaviate_url}")

        # Create custom configuration
        logger.info("⚙️  Creating custom configuration...")
        config = KnowledgeBaseManagerConfig(
            chunk_config=ChunkConfig(
                chunk_size=512, overlap_size=50, chunk_type="document"
            ),
            embedding_config=EmbeddingConfig(
                model_name="all-mpnet-base-v2", max_length=512
            ),
            database_manager_config=DatabaseManagerConfig(url=weaviate_url),
        )

        # Initialize knowledge base manager with custom config
        logger.info(
            "🚀 Initializing knowledge base manager with custom configuration..."
        )
        kbm = KnowledgeBaseManager(config=config)

        collection_name = "ragora_advanced_usage"

        # Create schema
        logger.info("📊 Creating vector store schema...")
        kbm.vector_store.create_schema(force_recreate=True, class_name=collection_name)

        # Add comprehensive sample data
        logger.info("📝 Adding comprehensive sample data...")
        sample_chunks = [
            DataChunk(
                chunk_id="physics_001",
                text="Einstein's theory of special relativity introduced the concept of time dilation.",
                start_idx=0,
                end_idx=80,
                metadata=ChunkMetadata(
                    chunk_idx=1,
                    chunk_size=80,
                    total_chunks=1,
                    created_at=datetime.now().isoformat(),
                    page_number=1,
                    section_title="Physics",
                ),
                source_document="physics_theory.tex",
                chunk_type="text",
            ),
            DataChunk(
                chunk_id="physics_002",
                text="The famous equation E = mc² shows the relationship between energy and mass.",
                start_idx=81,
                end_idx=150,
                metadata=ChunkMetadata(
                    chunk_idx=2,
                    chunk_size=69,
                    total_chunks=1,
                    created_at=datetime.now().isoformat(),
                    page_number=1,
                    section_title="Physics",
                ),
                source_document="physics_theory.tex",
                chunk_type="equation",
            ),
            DataChunk(
                chunk_id="physics_003",
                text="Quantum mechanics describes the behavior of matter at atomic and subatomic scales.",
                start_idx=151,
                end_idx=220,
                metadata=ChunkMetadata(
                    chunk_idx=3,
                    chunk_size=69,
                    total_chunks=1,
                    created_at=datetime.now().isoformat(),
                    page_number=1,
                    section_title="Physics",
                ),
                source_document="quantum_physics.tex",
                chunk_type="text",
            ),
            DataChunk(
                chunk_id="physics_004",
                text="Schrödinger's equation: iℏ∂ψ/∂t = Ĥψ describes quantum state evolution.",
                start_idx=221,
                end_idx=290,
                metadata=ChunkMetadata(
                    chunk_idx=4,
                    chunk_size=69,
                    total_chunks=1,
                    created_at=datetime.now().isoformat(),
                    page_number=1,
                    section_title="Physics",
                ),
                source_document="quantum_physics.tex",
                chunk_type="equation",
            ),
            DataChunk(
                chunk_id="physics_005",
                text="The uncertainty principle states that certain pairs of physical properties cannot be simultaneously measured.",
                start_idx=291,
                end_idx=370,
                metadata=ChunkMetadata(
                    chunk_idx=5,
                    chunk_size=69,
                    total_chunks=1,
                    created_at=datetime.now().isoformat(),
                    page_number=1,
                    section_title="Physics",
                ),
                source_document="quantum_physics.tex",
                chunk_type="text",
            ),
        ]

        # Store all chunks
        stored_uuids = kbm.vector_store.store_chunks(
            sample_chunks, class_name=collection_name
        )
        logger.info(f"✅ Stored {len(stored_uuids)} chunks")

        # Demonstrate different search types
        logger.info("🔍 Demonstrating different search types...")

        # 1. Vector similarity search
        logger.info("\n1️⃣ Vector Similarity Search:")
        similar_results = kbm.search_similar(
            "Einstein relativity equations", top_k=3, class_name=collection_name
        )
        for i, result in enumerate(similar_results, 1):
            logger.info(f"   {i}. Score: {result.get('similarity_score', 'N/A'):.3f}")
            logger.info(f"      Content: {result['content'][:60]}...")

        # 2. Hybrid search
        logger.info("\n2️⃣ Hybrid Search:")
        hybrid_results = kbm.search_hybrid(
            "quantum mechanics equations",
            alpha=0.7,
            top_k=3,
            class_name=collection_name,
        )
        for i, result in enumerate(hybrid_results, 1):
            logger.info(f"   {i}. Score: {result.get('hybrid_score', 'N/A'):.3f}")
            logger.info(f"      Content: {result['content'][:60]}...")

        # 3. Unified query with different search types
        logger.info("\n3️⃣ Unified Queries:")

        queries = [
            ("What equations did Einstein develop?", "hybrid"),
            ("What is quantum mechanics about?", "similar"),
        ]

        for question, search_type in queries:
            logger.info(f"\n   Question: {question}")
            logger.info(f"   Search type: {search_type}")

            response = kbm.query(
                question, search_type=search_type, top_k=2, class_name=collection_name
            )

            for i, chunk in enumerate(response["retrieved_chunks"], 1):
                logger.info(f"   {i}. {chunk['content'][:50]}...")

        # System statistics and monitoring
        logger.info("\n📊 System Statistics:")
        stats = kbm.get_system_stats(class_name=collection_name)

        logger.info(f"   System initialized: {stats['system_initialized']}")
        logger.info(f"   Total objects: {stats['vector_store']['total_objects']}")
        logger.info(f"   Embedding model: {stats['embedding_engine']['model_name']}")
        logger.info(f"   Chunk size: {stats['data_chunker']['chunk_size']}")
        logger.info(f"   Chunk overlap: {stats['data_chunker']['overlap_size']}")

        # Component access demonstration
        logger.info("\n🔧 Component Access:")

        # Direct access to specific chunk
        chunk_data = kbm.get_chunk("physics_002", class_name=collection_name)
        if chunk_data:
            logger.info(f"   Retrieved specific chunk: {chunk_data['content']}")

        # Test chunk deletion
        deleted = kbm.delete_chunk("physics_003", class_name=collection_name)
        if deleted:
            logger.info("   Successfully deleted chunk quantum_003")

        # Updated statistics
        updated_stats = kbm.get_system_stats(class_name=collection_name)
        logger.info(
            f"   Updated total objects: {updated_stats['vector_store']['total_objects']}"
        )

        logger.info("\n✅ Advanced usage example completed successfully!")
        logger.info("🎯 Key features demonstrated:")
        logger.info("   ✅ Custom configuration")
        logger.info("   ✅ Multiple search types")
        logger.info("   ✅ Component-level access")
        logger.info("   ✅ System monitoring")
        logger.info("   ✅ Data management")

    except Exception as e:
        logger.error(f"❌ Error in advanced usage example: {str(e)}")
        raise
    finally:
        # Clean up
        if "kbm" in locals():
            kbm.close()


if __name__ == "__main__":
    main()
