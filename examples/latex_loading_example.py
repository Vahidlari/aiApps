"""Document Processing Example with Knowledge Base Manager

This module demonstrates how to load and process LaTeX, Markdown, and plain text
documents using the knowledge
base manager system. It shows the complete workflow from document ingestion to
querying and retrieval.

Features demonstrated:
- LaTeX document processing and chunking
- Markdown document processing
- Plain text document processing
- Vector embedding generation
- Vector store integration with Weaviate
- Document querying and retrieval
- Multiple query examples with different complexity levels

Prerequisites:
1. Weaviate server must be running
   - Start: cd tools/database_server && ./database-manager.sh start
   - Status: ./database-manager.sh status
   - Stop: ./database-manager.sh stop

2. Sample files should exist at:
   - examples/latex_samples/sample_chapter.tex
   - examples/latex_samples/references.bib
   - examples/markdown_samples/sample_overview.md
   - examples/text_samples/sample_notes.txt

Configuration Notes:
- For Docker containers: use http://host.docker.internal:8080
- For local development: use http://localhost:8080
"""

import logging
import sys
from pathlib import Path

from ragora import (
    ChunkConfig,
    DatabaseManagerConfig,
    EmbeddingConfig,
    KnowledgeBaseManager,
    KnowledgeBaseManagerConfig,
    SearchStrategy,
)

# Configure logging with more detailed formatting
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

SAMPLE_LATEX_PATH = Path("examples/latex_samples/sample_chapter.tex")
SAMPLE_BIBLIOGRAPHY_PATH = Path("examples/latex_samples/references.bib")
SAMPLE_MARKDOWN_PATH = Path("examples/markdown_samples/sample_overview.md")
SAMPLE_TEXT_PATH = Path("examples/text_samples/sample_notes.txt")


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

    # Check required sample files
    sample_files = [
        (SAMPLE_LATEX_PATH, "Sample LaTeX file"),
        (SAMPLE_BIBLIOGRAPHY_PATH, "Sample bibliography file"),
        (SAMPLE_MARKDOWN_PATH, "Sample Markdown file"),
        (SAMPLE_TEXT_PATH, "Sample text file"),
    ]

    all_present = True
    for path, label in sample_files:
        if not path.exists():
            print(f"❌ {label} not found at: {path}")
            all_present = False
        else:
            print(f"✅ {label} found: {path}")

    if not all_present:
        print("   Please ensure all sample files exist before running this example.")
        return False

    print("\n💡 Make sure Weaviate server is running:")
    print("   cd tools/database_server")
    print("   ./database-manager.sh start")

    return True


def create_knowledge_base_manager_config() -> KnowledgeBaseManagerConfig:
    """Create and return the RAG configuration."""
    print_step(1, "Creating RAG Configuration")

    # Chunk configuration - determines how documents are split
    chunk_config = ChunkConfig(
        chunk_size=512,  # Size of each text chunk in characters
        overlap_size=50,  # Overlap between consecutive chunks
        chunk_type="document",  # Chunking type
    )
    print(
        f"📄 Chunk Config: {chunk_config.chunk_size} chars, "
        f"{chunk_config.overlap_size} overlap"
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

    config = KnowledgeBaseManagerConfig(
        chunk_config=chunk_config,
        embedding_config=embedding_config,
        database_manager_config=database_manager_config,
    )

    print("✅ Knowledge Base Manager configuration created successfully")
    return config


def demonstrate_document_processing(kbm: KnowledgeBaseManager) -> None:
    """Demonstrate document processing and ingestion across formats."""

    collection_name = "Latex_loading_example"
    print_step(2, "Processing Documents")

    try:
        collectionlist = kbm.list_collections()
        if collection_name in collectionlist:
            kbm.delete_collection(collection_name)
            print("✅ Existing example collection deleted successfully!")

        # Process the LaTeX document with bibliography support
        print(f"📖 Loading LaTeX document: {SAMPLE_LATEX_PATH}")
        latex_result = kbm.process_documents(
            [str(SAMPLE_LATEX_PATH), str(SAMPLE_BIBLIOGRAPHY_PATH)],
            collection=collection_name,
        )
        print("✅ LaTeX document processed successfully!")
        print(f"   📊 Stored chunk IDs: {latex_result}")

        # Process the Markdown document
        print(f"📘 Loading Markdown document: {SAMPLE_MARKDOWN_PATH}")
        markdown_result = kbm.process_document(
            str(SAMPLE_MARKDOWN_PATH),
            document_type="markdown",
            collection=collection_name,
        )
        print("✅ Markdown document processed successfully!")
        print(f"   📊 Stored chunk IDs: {markdown_result}")

        # Process the plain text document
        print(f"📝 Loading text document: {SAMPLE_TEXT_PATH}")
        text_result = kbm.process_document(
            str(SAMPLE_TEXT_PATH),
            document_type="text",
            collection=collection_name,
        )
        print("✅ Text document processed successfully!")
        print(f"   📊 Stored chunk IDs: {text_result}")

    except Exception as e:
        print(f"❌ Error processing documents: {e}")
        raise


def demonstrate_queries(kbm: KnowledgeBaseManager) -> None:
    """Demonstrate various types of queries using batch search."""
    print_step(3, "Demonstrating Query Capabilities (Batch Search)")

    # Define different types of queries to showcase capabilities
    query_info_list = [
        {
            "category": "Physics Concepts",
            "query": "What is the relationship between mass and energy?",
            "description": "Basic physics concept query",
        },
        {
            "category": "Mathematical Formulas",
            "query": "Show me the mathematical equations related to relativity",
            "description": "Formula and equation search",
        },
        {
            "category": "Conceptual Understanding",
            "query": "Explain the theory of special relativity in simple terms",
            "description": "Complex conceptual query",
        },
        {
            "category": "Historical Context",
            "query": "Who developed the theory of relativity and when?",
            "description": "Historical and biographical query",
        },
        {
            "category": "Questions from the Markdown document",
            "query": "How does markdown processing works in Ragora?",
            "description": "Question about Markdown processing",
        },
    ]

    # Extract query strings for batch search
    queries = [query_info["query"] for query_info in query_info_list]

    print("\n📦 Executing batch search for all queries...")
    try:
        # Execute batch search for all queries at once
        batch_results = kbm.batch_search(
            queries,
            strategy=SearchStrategy.HYBRID,
            collection="latex_loading_example",
        )

        # Process and display results
        for i, (query_info, response) in enumerate(
            zip(query_info_list, batch_results), 1
        ):
            print(f"\n🔍 Query {i}: {query_info['category']}")
            print(f"   Description: {query_info['description']}")
            print(f"   Question: \"{query_info['query']}\"")
            print("   " + "─" * 40)

            # Format the response nicely
            print("   📝 Answer:")
            print(f"   Strategy: {response.strategy}")
            print(
                f"   Found {response.total_found} chunks in "
                f"{response.execution_time:.3f}s"
            )

            if response.results:
                # Show the first result as the answer
                first_result = response.results[0]
                content = first_result.content

                # Split long responses into readable chunks
                words = content.split()
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

                # Show source information
                source_doc = (
                    first_result.properties.get("source_document")
                    or first_result.metadata.source_document
                )
                if source_doc:
                    print(f"   📄 Source: {source_doc}")
            else:
                print("      No relevant results found.")

            print()

    except Exception as e:
        print(f"   ❌ Error executing batch search: {e}")
        print()


def demonstrate_similarity_search(kbm: KnowledgeBaseManager) -> None:
    """Demonstrate similarity search capabilities."""
    print_step(4, "Demonstrating Similarity Search")

    # Use search terms relevant to the quantum mechanics content in the sample
    search_terms = [
        "Schrödinger equation",
        "quantum mechanics",
        "uncertainty principle",
        "energy conservation",  # This should return fewer/no results as it's
        "document processing",
        # not in the document
    ]

    for term in search_terms:
        print(f'\n🔎 Searching for: "{term}"')
        try:
            # Use the search method with SIMILAR strategy
            response = kbm.search(
                term,
                strategy=SearchStrategy.SIMILAR,
                top_k=3,
                collection="latex_loading_example",
            )
            results = response.results

            if results:
                print(f"   Found {len(results)} similar documents:")
                for i, result in enumerate(results, 1):
                    # Extract content from the result
                    content = result.content
                    similarity_score = result.similarity_score
                    content_preview = content[:100]
                    if len(content) > 100:
                        content_preview += "..."
                    print(
                        f"   {i}. {content_preview} (Similarity score: {similarity_score:.3f})"
                    )
            else:
                print("   No similar documents found.")
                if term == "energy conservation":
                    print("   ℹ️  Note: 'Energy conservation' not in document")
                    print("      in this quantum mechanics document, so no")
                    print("      results are expected.")

        except AttributeError:
            print(
                "   ⚠️  Similarity search not available in this Knowledge Base Manager system"
            )
            break
        except Exception as e:
            print(f"   ❌ Error in similarity search: {e}")


def demonstrate_keyword_search(kbm: KnowledgeBaseManager) -> None:
    """Demonstrate keyword search capabilities."""
    print_step(5, "Demonstrating Keyword Search")

    # Use search terms relevant to the quantum mechanics content in the sample
    search_terms = [
        "Schrödinger equation",
        "quantum mechanics",
        "uncertainty principle",
        "energy conservation",  # This should return fewer/no results as it's
        "Ragora",
        # not in the document
    ]

    for term in search_terms:
        print(f'\n🔎 Searching for: "{term}"')
        try:
            # Use the search method with KEYWORD strategy
            response = kbm.search(
                term,
                strategy=SearchStrategy.KEYWORD,
                top_k=3,
                collection="latex_loading_example",
            )
            results = response.results

            if results:
                print(f"   Found {len(results)} similar documents:")
                for i, result in enumerate(results, 1):
                    # Extract content from the result
                    content = result.content
                    bm25_score = result.bm25_score
                    content_preview = content[:100]
                    if len(content) > 100:
                        content_preview += "..."
                    print(f"   {i}. {content_preview} (BM25 score: {bm25_score:.3f})")
            else:
                print("   No similar documents found.")
                if term == "energy conservation":
                    print("   ℹ️  Note: 'Energy conservation' not in document")
                    print("      in this quantum mechanics document, so no")
                    print("      results are expected.")

        except AttributeError:
            print(
                "   ⚠️  Keyword search not available in this Knowledge Base Manager system"
            )
            break
        except Exception as e:
            print(f"   ❌ Error in keyword search: {e}")


def main():
    """Main function that orchestrates the LaTeX document processing example."""
    print_section_header("🚀 LaTeX Document Knowledge Base Manager System Demo")
    print(
        "This example demonstrates loading and querying LaTeX documents "
        "using Knowledge Base Manager"
    )
    print("(Retrieval-Augmented Generation) technology with Weaviate vector " "store.")

    # Check prerequisites
    if not check_prerequisites():
        print(
            "\n❌ Prerequisites not met. Please fix the issues above and try " "again."
        )
        sys.exit(1)

    try:
        # Step 1: Create Knowledge Base Manager configuration
        config = create_knowledge_base_manager_config()

        # Step 2: Initialize knowledge base manager
        print_step(2, "Initializing Knowledge Base Manager")
        kbm = KnowledgeBaseManager(config=config)
        print("✅ Knowledge base manager initialized successfully")

        # Step 3: Process documents across formats
        demonstrate_document_processing(kbm)

        # Step 4: Demonstrate queries
        demonstrate_queries(kbm)

        # Step 5: Demonstrate similarity search (if available)
        demonstrate_similarity_search(kbm)

        # Step 6: Demonstrate keyword search
        demonstrate_keyword_search(kbm)

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
