#!/usr/bin/env python3
"""Advanced usage example for the knowledge base manager package.

This example demonstrates advanced usage with custom configuration:
1. Custom configuration setup
2. Modern chunking using DataChunker and ChunkingContextBuilder
3. Multiple chunking strategies (document, email, text)
4. Different search types
5. System monitoring and statistics

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
    ChunkingContextBuilder,
    DatabaseManagerConfig,
    DataChunker,
    EmbeddingConfig,
    FilterBuilder,
    KnowledgeBaseManager,
    KnowledgeBaseManagerConfig,
    SearchStrategy,
)

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
        kbm.vector_store.create_schema(force_recreate=True, collection=collection_name)

        # Add comprehensive sample data using modern chunking approach
        logger.info("📝 Adding comprehensive sample data using modern chunking...")

        # Create a chunker instance
        chunker = DataChunker()

        # Sample documents content
        physics_document = """
        Einstein's theory of special relativity introduced the concept of time dilation.
        The famous equation E = mc² shows the relationship between energy and mass.
        This revolutionary theory changed our understanding of space and time.
        """

        quantum_document = """
        Quantum mechanics describes the behavior of matter at atomic and subatomic scales.
        Schrödinger's equation: iℏ∂ψ/∂t = Ĥψ describes quantum state evolution.
        The uncertainty principle states that certain pairs of physical properties cannot be simultaneously measured.
        Wave-particle duality is a fundamental concept in quantum physics.
        """

        computer_science_document = """
        Computer science is the study of computation, algorithms, and information processing.
        The Turing machine is a theoretical model of computation.
        The halting problem is a fundamental problem in computer science.
        """

        von_neumann_document = """
        John von Neumann was a Hungarian-American mathematician and computer scientist.
        He is known for his contributions to the development of the modern computer.
        He is also known for his contributions to the development of the theory of computation.
        """

        karl_popper_document = """
        Karl Popper was an Austrian–British[5] philosopher, academic and social commentator.
        One of the 20th century's most influential philosophers of science, Popper is known for 
        his rejection of the classical inductivist views on the scientific method in favour of 
        empirical falsification made possible by his falsifiability criterion, and for founding 
        the Department of Philosophy at the London School of Economics and Political Science.
        """

        # Create chunks using ChunkingContextBuilder
        sample_chunks = []

        # Physics document chunks
        physics_context = (
            ChunkingContextBuilder()
            .for_document()
            .with_source("physics_theory.tex")
            .with_page(1)
            .with_section("Physics")
            .with_created_at(datetime.now().isoformat())
            .with_start_chunk_id(0)
            .build()
        )
        physics_chunks = chunker.chunk(physics_document, physics_context)
        sample_chunks.extend(physics_chunks)

        # Quantum physics document chunks
        quantum_context = (
            ChunkingContextBuilder()
            .for_document()
            .with_source("quantum_physics.tex")
            .with_page(1)
            .with_section("Quantum Physics")
            .with_created_at(datetime.now().isoformat())
            .with_start_chunk_id(len(physics_chunks))
            .build()
        )
        quantum_chunks = chunker.chunk(quantum_document, quantum_context)
        sample_chunks.extend(quantum_chunks)

        computer_science_context = (
            ChunkingContextBuilder()
            .for_document()
            .with_source("computer_science.tex")
            .with_page(1)
            .with_section("Computer Science")
            .with_created_at(datetime.now().isoformat())
            .with_start_chunk_id(len(quantum_chunks))
            .build()
        )
        computer_science_chunks = chunker.chunk(
            computer_science_document, computer_science_context
        )
        sample_chunks.extend(computer_science_chunks)

        von_neumann_context = (
            ChunkingContextBuilder()
            .for_document()
            .with_source("von_neumann.tex")
            .with_page(1)
            .with_section("Von Neumann")
            .with_created_at(datetime.now().isoformat())
            .with_start_chunk_id(len(computer_science_chunks))
            .build()
        )
        von_neumann_chunks = chunker.chunk(von_neumann_document, von_neumann_context)
        sample_chunks.extend(von_neumann_chunks)

        karl_popper_context = (
            ChunkingContextBuilder()
            .for_document()
            .with_source("karl_popper.tex")
            .with_page(1)
            .with_section("Karl Popper")
            .with_created_at(datetime.now().isoformat())
            .with_start_chunk_id(len(von_neumann_chunks))
            .build()
        )
        karl_popper_chunks = chunker.chunk(karl_popper_document, karl_popper_context)
        sample_chunks.extend(karl_popper_chunks)

        # Add comprehensive examples with custom metadata and email support
        logger.info("📧 Adding email and custom metadata examples...")

        # Email example with full metadata
        email_content = """
        Hi Team,

        I wanted to update everyone on our project progress. We've completed the initial 
        research phase and are now moving into the development phase. The timeline looks 
        good and we should be able to deliver on schedule.

        Key points:
        - Research phase completed ahead of schedule
        - Development phase starting next week
        - Budget is on track
        - Team morale is high

        Let me know if you have any questions.

        Best regards,
        Project Manager
        """

        email_context = (
            ChunkingContextBuilder()
            .for_email()
            .with_email_info(
                subject="Project Update - Q1 Progress",
                sender="project.manager@company.com",
                recipient="team@company.com",
                email_id="msg_2024_001",
                email_date="2024-01-15T14:30:00Z",
                email_folder="work/projects",
            )
            .with_custom_metadata(
                {
                    "language": "en",
                    "domain": "business",
                    "confidence": 0.92,
                    "tags": ["project", "update", "progress", "team"],
                    "priority": 3,
                    "content_category": "project_communication",
                    "department": "engineering",
                    "project_id": "PROJ-2024-001",
                }
            )
            .with_start_sequence_idx(len(sample_chunks))
            .build()
        )
        email_chunks = chunker.chunk(email_content, email_context)
        sample_chunks.extend(email_chunks)

        # Document with rich custom metadata
        legal_document = """
        This agreement ("Agreement") is entered into between Company A and Company B 
        for the provision of software development services. The terms and conditions 
        outlined herein shall govern the relationship between the parties.
        """

        legal_context = (
            ChunkingContextBuilder()
            .for_document()
            .with_source("service_agreement.pdf")
            .with_page(1)
            .with_section("Terms and Conditions")
            .with_created_at("2024-01-10T09:00:00Z")
            .with_custom_metadata(
                {
                    "language": "en",
                    "domain": "legal",
                    "confidence": 0.98,
                    "tags": ["contract", "agreement", "legal", "services"],
                    "priority": 5,
                    "content_category": "legal_document",
                    "document_type": "service_agreement",
                    "jurisdiction": "US",
                    "effective_date": "2024-01-10",
                    "parties": ["Company A", "Company B"],
                }
            )
            .with_start_sequence_idx(len(sample_chunks))
            .build()
        )
        legal_chunks = chunker.chunk(legal_document, legal_context)
        sample_chunks.extend(legal_chunks)

        # Mixed content with different metadata patterns
        code_document = """
        def calculate_fibonacci(n):
            if n <= 1:
                return n
            return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
        
        This is a recursive implementation of the Fibonacci sequence.
        """

        code_context = (
            ChunkingContextBuilder()
            .for_document()
            .with_source("algorithms.py")
            .with_page(1)
            .with_section("Mathematical Algorithms")
            .with_created_at("2024-01-12T16:45:00Z")
            .with_custom_metadata(
                {
                    "language": "en",
                    "domain": "technical",
                    "confidence": 0.95,
                    "tags": ["python", "algorithm", "fibonacci", "recursion"],
                    "priority": 4,
                    "content_category": "code_example",
                    "programming_language": "python",
                    "complexity": "exponential",
                    "difficulty": "intermediate",
                }
            )
            .with_start_sequence_idx(len(sample_chunks))
            .build()
        )
        code_chunks = chunker.chunk(code_document, code_context)
        sample_chunks.extend(code_chunks)

        logger.info(
            f"Created {len(sample_chunks)} chunks using modern chunking approach with custom metadata"
        )

        # Demonstrate different chunking strategies
        logger.info("🔧 Demonstrating different chunking strategies...")

        # Email chunking example
        email_content = """
        Subject: Project Update Meeting

        Hi Team,

        I wanted to update everyone on our project progress. We've completed the initial
        research phase and are moving into the development stage. The next milestone is
        scheduled for next Friday.

        Best regards,
        Project Manager
        """

        email_context = (
            ChunkingContextBuilder()
            .for_email()
            .with_email_info(
                subject="Project Update Meeting",
                sender="manager@company.com",
                recipient="team@company.com",
                email_id="msg_001",
                email_date=datetime.now().isoformat(),
                email_folder="inbox",
            )
            .with_start_chunk_id(len(sample_chunks))
            .build()
        )
        email_chunks = chunker.chunk(email_content, email_context)
        sample_chunks.extend(email_chunks)

        # Text chunking example (general content)
        general_text = """
        This is a general text document that doesn't fit into specific categories.
        It contains various topics and information that would be processed using
        the default text chunking strategy.
        """

        text_context = (
            ChunkingContextBuilder()
            .for_text()
            .with_source("general_content.txt")
            .with_start_chunk_id(len(sample_chunks))
            .build()
        )
        text_chunks = chunker.chunk(general_text, text_context)
        sample_chunks.extend(text_chunks)

        logger.info(f"Total chunks created: {len(sample_chunks)}")
        logger.info(
            f"  - Document chunks: {len(physics_chunks + quantum_chunks + computer_science_chunks + von_neumann_chunks + karl_popper_chunks)}"
        )
        # Store all chunks
        stored_uuids = kbm.vector_store.store_chunks(
            sample_chunks, collection=collection_name
        )
        logger.info(f"✅ Stored {len(stored_uuids)} chunks")

        # Demonstrate different search types
        logger.info("🔍 Demonstrating different search types...")

        # 1. Vector similarity search
        logger.info("\n1️⃣ Vector Similarity Search:")
        similar_response = kbm.search(
            "computer science and quantum physics",
            strategy=SearchStrategy.SIMILAR,
            top_k=3,
            collection=collection_name,
        )
        for i, result in enumerate(similar_response.results, 1):
            logger.info(f"   {i}. Score: {result.similarity_score:.3f}")
            logger.info(f"      Content: {result.content[:60]}...")
            # Show metadata if available
            metadata = result.metadata
            if metadata.language:
                logger.info(
                    f"      Language: {metadata.language}, "
                    f"Domain: {metadata.domain}"
                )
            if metadata.email_subject:
                logger.info(
                    f"      Email: {metadata.email_subject} from "
                    f"{metadata.email_sender}"
                )

        # 2. Hybrid search
        logger.info("\n2️⃣ Hybrid Search:")
        hybrid_response = kbm.search(
            "computer science and quantum physics",
            strategy=SearchStrategy.HYBRID,
            alpha=0.7,
            top_k=3,
            collection=collection_name,
        )
        for i, result in enumerate(hybrid_response.results, 1):
            hybrid_score = result.hybrid_score or 0.0
            logger.info(f"   {i}. Score: {hybrid_score:.3f}")
            logger.info(f"      Content: {result.content[:60]}...")
            # Show metadata if available
            metadata = result.metadata
            if metadata.language:
                logger.info(
                    f"      Language: {metadata.language}, "
                    f"Domain: {metadata.domain}"
                )
            if metadata.email_subject:
                logger.info(
                    f"      Email: {metadata.email_subject} from "
                    f"{metadata.email_sender}"
                )

        # 3. Unified query with different search types
        logger.info("\n3️⃣ Unified Queries:")

        queries = [
            ("What equations did Einstein develop?", "hybrid"),
            ("What is computer science about?", "similar"),
        ]

        for question, search_type in queries:
            logger.info(f"\n   Question: {question}")
            logger.info(f"   Search type: {search_type}")

            response = kbm.search(
                question,
                strategy=SearchStrategy(search_type),
                top_k=2,
                collection=collection_name,
            )

            for i, chunk in enumerate(response.results, 1):
                logger.info(f"   {i}. {chunk.content[:50]}...")

        # 4. Filter examples
        logger.info("\n4️⃣ Filter Examples:")

        # Filter by chunk type
        logger.info("\n   Filter by chunk type (text only):")
        text_filter = FilterBuilder.by_chunk_type("text")
        filtered_results = kbm.search(
            "computer science",
            strategy=SearchStrategy.HYBRID,
            top_k=5,
            collection=collection_name,
            filter=text_filter,
        )
        logger.info(f"   Found {filtered_results.total_found} text chunks")
        for i, result in enumerate(filtered_results.results[:2], 1):
            logger.info(f"   {i}. {result.content[:50]}...")

        # Filter by source document
        logger.info("\n   Filter by source document:")
        doc_filter = FilterBuilder.by_source_document("physics_paper.tex")
        doc_results = kbm.search(
            "quantum mechanics",
            strategy=SearchStrategy.HYBRID,
            top_k=3,
            collection=collection_name,
            filter=doc_filter,
        )
        logger.info(f"   Found {doc_results.total_found} chunks from physics_paper.tex")

        # Filter by date range
        logger.info("\n   Filter by date range (2024 documents):")
        date_filter = FilterBuilder.by_date_range(start="2024-01-01", end="2024-12-31")
        date_results = kbm.search(
            "research findings",
            strategy=SearchStrategy.HYBRID,
            top_k=3,
            collection=collection_name,
            filter=date_filter,
        )
        logger.info(f"   Found {date_results.total_found} chunks from 2024")

        # Filter by email sender
        logger.info("\n   Filter by email sender:")
        email_filter = FilterBuilder.by_email_sender("project.manager@company.com")
        email_results = kbm.search(
            "project update",
            strategy=SearchStrategy.HYBRID,
            top_k=3,
            collection=collection_name,
            filter=email_filter,
        )
        logger.info(
            f"   Found {email_results.total_found} emails from project.manager@company.com"
        )

        # Combined filters (AND logic)
        logger.info("\n   Combined filters (text chunks from specific document):")
        type_filter = FilterBuilder.by_chunk_type("text")
        source_filter = FilterBuilder.by_source_document("physics_paper.tex")
        combined_filter = FilterBuilder.combine_and(type_filter, source_filter)
        combined_results = kbm.search(
            "physics concepts",
            strategy=SearchStrategy.HYBRID,
            top_k=3,
            collection=collection_name,
            filter=combined_filter,
        )
        logger.info(
            f"   Found {combined_results.total_found} text chunks from physics_paper.tex"
        )

        # Filter by page number
        logger.info("\n   Filter by page number:")
        page_filter = FilterBuilder.by_page_number(1)
        page_results = kbm.search(
            "introduction",
            strategy=SearchStrategy.HYBRID,
            top_k=3,
            collection=collection_name,
            filter=page_filter,
        )
        logger.info(f"   Found {page_results.total_found} chunks from page 1")

        # Advanced: Email date range filter
        logger.info("\n   Filter by email date range:")
        email_date_filter = FilterBuilder.by_email_date_range(
            start="2024-01-01", end="2024-01-31"
        )
        email_date_results = kbm.search(
            "project",
            strategy=SearchStrategy.HYBRID,
            top_k=3,
            collection=collection_name,
            filter=email_date_filter,
        )
        logger.info(
            f"   Found {email_date_results.total_found} emails from January 2024"
        )

        # System statistics and monitoring
        logger.info("\n📊 System Statistics:")
        stats = kbm.get_collection_stats(collection=collection_name)

        logger.info(f"   System initialized: {stats['system_initialized']}")
        logger.info(f"   Total objects: {stats['vector_store']['total_objects']}")
        logger.info(f"   Embedding model: {stats['embedding_engine']['model_name']}")
        logger.info(f"   Chunk size: {stats['data_chunker']['chunk_size']}")
        logger.info(f"   Chunk overlap: {stats['data_chunker']['overlap_size']}")

        # Component access demonstration
        logger.info("\n🔧 Component Access:")

        # Direct access to specific chunk (using first chunk's ID)
        if sample_chunks:
            first_chunk_id = sample_chunks[0].chunk_id
            chunk_data = kbm.get_chunk(first_chunk_id, collection=collection_name)
            if chunk_data:
                logger.info(
                    f"   Retrieved specific chunk: {chunk_data.content[:50]}..."
                )

        # Test chunk deletion (using second chunk's ID if available)
        if len(sample_chunks) > 1:
            second_chunk_id = sample_chunks[1].chunk_id
            deleted = kbm.delete_chunk(second_chunk_id, collection=collection_name)
            if deleted:
                logger.info(f"   Successfully deleted chunk {second_chunk_id}")

        # Updated statistics
        updated_stats = kbm.get_collection_stats(collection=collection_name)
        logger.info(
            f"   Updated total objects: {updated_stats['vector_store']['total_objects']}"
        )

        logger.info("\n✅ Advanced usage example completed successfully!")
        logger.info("🎯 Key features demonstrated:")
        logger.info("   ✅ Custom configuration")
        logger.info("   ✅ Modern chunking with DataChunker and ChunkingContextBuilder")
        logger.info("   ✅ Multiple chunking strategies (document, email, text)")
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
