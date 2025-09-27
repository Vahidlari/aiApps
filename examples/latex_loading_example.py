"""LaTeX Document Processing Example with RAG System

This module demonstrates how to load and process LaTeX documents using the RAG
(Retrieval-Augmented Generation) system. It shows the complete workflow from
document ingestion to querying and retrieval.

Features demonstrated:
- LaTeX document processing and chunking
- Vector embedding generation
- Vector store integration with Weaviate
- Document querying and retrieval
- Multiple query examples with different complexity levels

Prerequisites:
1. Weaviate server must be running
   - Start: cd tools/database_server && ./database-manager.sh start
   - Status: ./database-manager.sh status
   - Stop: ./database-manager.sh stop

2. Sample LaTeX file should exist at: examples/latex_samples/sample_chapter.tex

Configuration Notes:
- For Docker containers: use http://host.docker.internal:8080
- For local development: use http://localhost:8080
"""

import logging
import sys
from pathlib import Path

from ragnarock import (
    ChunkConfig,
    DatabaseManagerConfig,
    EmbeddingConfig,
    RAGConfig,
    RAGSystem,
)

# Configure logging with more detailed formatting
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def print_section_header(title: str, width: int = 60) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * width)
    print(f" {title} ".center(width))
    print("=" * width)


def print_step(step_num: int, description: str) -> None:
    """Print a formatted step description."""
    print(f"\n📋 Step {step_num}: {description}")
    print("-" * 50)


def check_prerequisites() -> bool:
    """Check if all prerequisites are met."""
    print_section_header("🔍 Checking Prerequisites")

    # Check if sample file exists
    sample_file = Path("examples/latex_samples/sample_chapter.tex")
    if not sample_file.exists():
        print(f"❌ Sample LaTeX file not found at: {sample_file}")
        print("   Please ensure the sample file exists before running this" " example.")
        return False
    else:
        print(f"✅ Sample LaTeX file found: {sample_file}")

    print("\n💡 Make sure Weaviate server is running:")
    print("   cd tools/database_server")
    print("   ./database-manager.sh start")

    return True


def create_rag_config() -> RAGConfig:
    """Create and return the RAG configuration."""
    print_step(1, "Creating RAG Configuration")

    # Chunk configuration - determines how documents are split
    chunk_config = ChunkConfig(
        chunk_size=512,  # Size of each text chunk in characters
        overlap=50,  # Overlap between consecutive chunks
        strategy="adaptive_fixed_size",  # Chunking strategy
    )
    print(
        f"📄 Chunk Config: {chunk_config.chunk_size} chars, "
        f"{chunk_config.overlap} overlap"
    )

    # Embedding configuration - determines how text is vectorized
    embedding_config = EmbeddingConfig(
        model_name="all-mpnet-base-v2",  # Pre-trained sentence transformer
        max_length=512,  # Maximum sequence length for the model
    )
    print(f"🧠 Embedding Model: {embedding_config.model_name}")

    # Vector store configuration - determines where vectors are stored
    database_manager_config = DatabaseManagerConfig(
        url="http://host.docker.internal:8080",  # Weaviate server URL
        grpc_port=50051,  # gRPC port for Weaviate connection
        timeout=30,  # Request timeout in seconds
    )
    print(f"🗄️  Vector Store: {database_manager_config.url}")

    config = RAGConfig(
        chunk_config=chunk_config,
        embedding_config=embedding_config,
        database_manager_config=database_manager_config,
    )

    print("✅ RAG configuration created successfully")
    return config


def demonstrate_document_processing(
    rag: RAGSystem, file_path: str, bibliography_path: str
) -> None:
    """Demonstrate document processing and ingestion."""
    print_step(2, "Processing LaTeX Document")

    print(f"📖 Loading document: {file_path}")

    try:
        # Process the LaTeX document
        result = rag.process_documents([file_path, bibliography_path])
        print("✅ Document processed successfully!")
        print(f"📊 Processing result: {result}")

    except Exception as e:
        print(f"❌ Error processing document: {e}")
        raise


def demonstrate_queries(rag: RAGSystem) -> None:
    """Demonstrate various types of queries."""
    print_step(3, "Demonstrating Query Capabilities")

    # Define different types of queries to showcase capabilities
    queries = [
        {
            "category": "Physics Concepts",
            "query": "What is the relationship between mass and energy?",
            "description": "Basic physics concept query",
        },
        {
            "category": "Mathematical Formulas",
            "query": "Show me the mathematical equations related to " "relativity",
            "description": "Formula and equation search",
        },
        {
            "category": "Conceptual Understanding",
            "query": "Explain the theory of special relativity in simple " "terms",
            "description": "Complex conceptual query",
        },
        {
            "category": "Historical Context",
            "query": "Who developed the theory of relativity and when?",
            "description": "Historical and biographical query",
        },
    ]

    for i, query_info in enumerate(queries, 1):
        print(f"\n🔍 Query {i}: {query_info['category']}")
        print(f"   Description: {query_info['description']}")
        print(f"   Question: \"{query_info['query']}\"")
        print("   " + "─" * 40)

        try:
            # Execute the query
            response = rag.query(query_info["query"])

            # Format the response nicely
            print("   📝 Answer:")
            if isinstance(response, str):
                # Split long responses into readable chunks
                words = response.split()
                lines = []
                current_line = ""

                for word in words:
                    if len(current_line + " " + word) > 80:
                        if current_line:
                            lines.append(current_line)
                        current_line = word
                    else:
                        current_line += (" " + word) if current_line else word

                if current_line:
                    lines.append(current_line)

                for line in lines:
                    print(f"      {line}")
            else:
                print(f"      {response}")

        except Exception as e:
            print(f"   ❌ Error executing query: {e}")

        print()


def demonstrate_similarity_search(rag: RAGSystem) -> None:
    """Demonstrate similarity search capabilities."""
    print_step(4, "Demonstrating Similarity Search")

    # Use search terms relevant to the quantum mechanics content in the sample
    search_terms = [
        "Schrödinger equation",
        "quantum mechanics",
        "uncertainty principle",
        "energy conservation",  # This should return fewer/no results as it's
        # not in the document
    ]

    for term in search_terms:
        print(f'\n🔎 Searching for: "{term}"')
        try:
            # Use the correct method name: search_similar
            results = rag.search_similar(term, top_k=3)

            if results:
                print(f"   Found {len(results)} similar documents:")
                for i, result in enumerate(results, 1):
                    # Extract content from the result dictionary
                    content = result.get("content", str(result))
                    if isinstance(content, str):
                        content_preview = content[:100]
                        if len(content) > 100:
                            content_preview += "..."
                        print(f"   {i}. {content_preview}")
                    else:
                        print(f"   {i}. {result}")
            else:
                print("   No similar documents found.")
                if term == "energy conservation":
                    print("   ℹ️  Note: 'Energy conservation' not in document")
                    print("      in this quantum mechanics document, so no")
                    print("      results are expected.")

        except AttributeError:
            print("   ⚠️  Similarity search not available in this RAG system")
            break
        except Exception as e:
            print(f"   ❌ Error in similarity search: {e}")


def main():
    """Main function that orchestrates the LaTeX document processing example."""
    print_section_header("🚀 LaTeX Document RAG System Demo")
    print("This example demonstrates loading and querying LaTeX documents " "using RAG")
    print("(Retrieval-Augmented Generation) technology with Weaviate vector " "store.")

    # Check prerequisites
    if not check_prerequisites():
        print(
            "\n❌ Prerequisites not met. Please fix the issues above and try " "again."
        )
        sys.exit(1)

    try:
        # Step 1: Create RAG configuration
        config = create_rag_config()

        # Step 2: Initialize RAG system
        print_step(2, "Initializing RAG System")
        rag = RAGSystem(config=config)
        print("✅ RAG system initialized successfully")

        # Step 3: Process document
        sample_file = "examples/latex_samples/sample_chapter.tex"
        bibliography_file = "examples/latex_samples/references.bib"
        demonstrate_document_processing(rag, sample_file, bibliography_file)

        # Step 4: Demonstrate queries
        demonstrate_queries(rag)

        # Step 5: Demonstrate similarity search (if available)
        demonstrate_similarity_search(rag)

        # Final summary
        print_section_header("🎉 Demo Completed Successfully")
        print("The LaTeX document has been processed and is ready for " "querying!")
        print("\n💡 Tips for further exploration:")
        print("   • Try different chunk sizes and overlap values")
        print("   • Experiment with different embedding models")
        print("   • Add more documents to build a larger knowledge base")
        print("   • Use more complex queries to test the system's " "capabilities")

    except Exception as e:
        print_section_header("❌ Error Occurred")
        print(f"An error occurred during execution: {e}")
        logger.exception("Detailed error information:")
        sys.exit(1)


if __name__ == "__main__":
    main()
