#!/usr/bin/env python3
"""Advanced usage example for the RAG system package.

This example demonstrates advanced usage with custom configuration:
1. Custom configuration setup
2. Multiple document processing
3. Different search types
4. System monitoring and statistics

Prerequisites:
- Weaviate running on localhost:8080
- Docker command: docker run -d --name weaviate -p 8080:8080 semitechnologies/weaviate:1.22.4
"""

import logging

from rag_system_package import (
    ChunkConfig,
    DataChunk,
    EmbeddingConfig,
    RAGConfig,
    RAGSystem,
    VectorStoreConfig,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Advanced usage example."""
    try:
        # Create custom configuration
        logger.info("⚙️  Creating custom configuration...")
        config = RAGConfig(
            chunk_config=ChunkConfig(
                chunk_size=512, overlap=50, strategy="adaptive_fixed_size"
            ),
            embedding_config=EmbeddingConfig(
                model_name="all-mpnet-base-v2", max_length=512
            ),
            vector_store_config=VectorStoreConfig(
                url="http://localhost:8080", class_name="AdvancedDocument", timeout=30
            ),
        )

        # Initialize RAG system with custom config
        logger.info("🚀 Initializing RAG system with custom configuration...")
        rag = RAGSystem(config=config)

        # Create schema
        logger.info("📊 Creating vector store schema...")
        rag.vector_store.create_schema(force_recreate=True)

        # Add comprehensive sample data
        logger.info("📝 Adding comprehensive sample data...")
        sample_chunks = [
            DataChunk(
                text="Einstein's theory of special relativity introduced the concept of time dilation.",
                start_idx=0,
                end_idx=80,
                metadata=None,
                chunk_id="relativity_001",
                source_document="physics_theory.tex",
                chunk_type="text",
            ),
            DataChunk(
                text="The famous equation E = mc² shows the relationship between energy and mass.",
                start_idx=81,
                end_idx=150,
                metadata=None,
                chunk_id="relativity_002",
                source_document="physics_theory.tex",
                chunk_type="equation",
            ),
            DataChunk(
                text="Quantum mechanics describes the behavior of matter at atomic and subatomic scales.",
                start_idx=151,
                end_idx=220,
                metadata=None,
                chunk_id="quantum_001",
                source_document="quantum_physics.tex",
                chunk_type="text",
            ),
            DataChunk(
                text="Schrödinger's equation: iℏ∂ψ/∂t = Ĥψ describes quantum state evolution.",
                start_idx=221,
                end_idx=290,
                metadata=None,
                chunk_id="quantum_002",
                source_document="quantum_physics.tex",
                chunk_type="equation",
            ),
            DataChunk(
                text="The uncertainty principle states that certain pairs of physical properties cannot be simultaneously measured.",
                start_idx=291,
                end_idx=370,
                metadata=None,
                chunk_id="quantum_003",
                source_document="quantum_physics.tex",
                chunk_type="text",
            ),
        ]

        # Store all chunks
        stored_uuids = rag.vector_store.store_chunks(sample_chunks)
        logger.info(f"✅ Stored {len(stored_uuids)} chunks")

        # Demonstrate different search types
        logger.info("🔍 Demonstrating different search types...")

        # 1. Vector similarity search
        logger.info("\n1️⃣ Vector Similarity Search:")
        similar_results = rag.search_similar("Einstein relativity equations", top_k=3)
        for i, result in enumerate(similar_results, 1):
            logger.info(f"   {i}. Score: {result.get('similarity_score', 'N/A'):.3f}")
            logger.info(f"      Content: {result['content'][:60]}...")

        # 2. Hybrid search
        logger.info("\n2️⃣ Hybrid Search:")
        hybrid_results = rag.search_hybrid(
            "quantum mechanics equations", alpha=0.7, top_k=3
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

            response = rag.query(question, search_type=search_type, top_k=2)

            for i, chunk in enumerate(response["retrieved_chunks"], 1):
                logger.info(f"   {i}. {chunk['content'][:50]}...")

        # System statistics and monitoring
        logger.info("\n📊 System Statistics:")
        stats = rag.get_system_stats()

        logger.info(f"   System initialized: {stats['system_initialized']}")
        logger.info(f"   Total objects: {stats['vector_store']['total_objects']}")
        logger.info(f"   Embedding model: {stats['embedding_engine']['model_name']}")
        logger.info(f"   Chunk size: {stats['data_chunker']['chunk_size']}")
        logger.info(f"   Chunk overlap: {stats['data_chunker']['overlap']}")

        # Component access demonstration
        logger.info("\n🔧 Component Access:")

        # Direct access to specific chunk
        chunk_data = rag.get_chunk("relativity_002")
        if chunk_data:
            logger.info(f"   Retrieved specific chunk: {chunk_data['content']}")

        # Test chunk deletion
        deleted = rag.delete_chunk("quantum_003")
        if deleted:
            logger.info("   Successfully deleted chunk quantum_003")

        # Updated statistics
        updated_stats = rag.get_system_stats()
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
        if "rag" in locals():
            rag.close()


if __name__ == "__main__":
    main()
