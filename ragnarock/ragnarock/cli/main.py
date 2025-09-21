"""Command-line interface for the RAG system."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from ..config.settings import ChunkConfig, EmbeddingConfig, RAGConfig, VectorStoreConfig
from ..core.rag_system import RAGSystem
from ..exceptions import RAGSystemError


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def process_document_command(args) -> None:
    """Process a LaTeX document."""
    try:
        config = RAGConfig(
            chunk_config=ChunkConfig(chunk_size=args.chunk_size, overlap=args.overlap),
            embedding_config=EmbeddingConfig(model_name=args.embedding_model),
            vector_store_config=VectorStoreConfig(
                url=args.weaviate_url, class_name=args.class_name
            ),
        )

        rag = RAGSystem(config=config)
        chunk_ids = rag.process_document(args.document)
        print(f"✅ Processed document: {args.document}")
        print(f"📄 Stored {len(chunk_ids)} chunks")

    except Exception as e:
        print(f"❌ Error processing document: {e}", file=sys.stderr)
        sys.exit(1)


def query_command(args) -> None:
    """Query the RAG system."""
    try:
        config = RAGConfig(
            chunk_config=ChunkConfig(),
            embedding_config=EmbeddingConfig(model_name=args.embedding_model),
            vector_store_config=VectorStoreConfig(
                url=args.weaviate_url, class_name=args.class_name
            ),
        )

        rag = RAGSystem(config=config)
        response = rag.query(
            args.question, search_type=args.search_type, top_k=args.top_k
        )

        print(f"❓ Question: {response['question']}")
        print(f"🔍 Search type: {response['search_type']}")
        print(f"📊 Retrieved {response['num_chunks']} chunks:")
        print()

        for i, chunk in enumerate(response["retrieved_chunks"], 1):
            print(f"{i}. 📝 {chunk['content'][:100]}...")
            if "similarity_score" in chunk:
                print(f"   📈 Similarity: {chunk['similarity_score']:.3f}")
            print()

    except Exception as e:
        print(f"❌ Error querying system: {e}", file=sys.stderr)
        sys.exit(1)


def status_command(args) -> None:
    """Check system status."""
    try:
        config = RAGConfig.default()
        rag = RAGSystem(config=config)
        stats = rag.get_system_stats()

        print("🔍 RAG System Status:")
        print(f"✅ Initialized: {stats['system_initialized']}")
        print(f"📊 Total objects: {stats['vector_store']['total_objects']}")
        print(f"🤖 Embedding model: {stats['embedding_engine']['model_name']}")
        print(f"📦 Chunk size: {stats['data_chunker']['chunk_size']}")

    except Exception as e:
        print(f"❌ Error checking status: {e}", file=sys.stderr)
        sys.exit(1)


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="RAG System CLI - LaTeX Document Knowledge Base",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a LaTeX document
  rag-system process document.tex
  
  # Query the knowledge base
  rag-system query "What is the main equation in chapter 2?"
  
  # Check system status
  rag-system status
        """,
    )

    # Global options
    parser.add_argument(
        "--weaviate-url",
        default="http://localhost:8080",
        help="Weaviate server URL (default: http://localhost:8080)",
    )
    parser.add_argument(
        "--class-name",
        default="Document",
        help="Weaviate class name (default: Document)",
    )
    parser.add_argument(
        "--embedding-model",
        default="all-mpnet-base-v2",
        help="Embedding model name (default: all-mpnet-base-v2)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Process document command
    process_parser = subparsers.add_parser("process", help="Process a LaTeX document")
    process_parser.add_argument("document", help="Path to LaTeX document")
    process_parser.add_argument(
        "--chunk-size",
        type=int,
        default=768,
        help="Chunk size in tokens (default: 768)",
    )
    process_parser.add_argument(
        "--overlap",
        type=int,
        default=100,
        help="Chunk overlap in tokens (default: 100)",
    )
    process_parser.set_defaults(func=process_document_command)

    # Query command
    query_parser = subparsers.add_parser("query", help="Query the knowledge base")
    query_parser.add_argument("question", help="Question to ask")
    query_parser.add_argument(
        "--search-type",
        choices=["similar", "hybrid"],
        default="hybrid",
        help="Type of search to perform (default: hybrid)",
    )
    query_parser.add_argument(
        "--top-k", type=int, default=5, help="Number of results to return (default: 5)"
    )
    query_parser.set_defaults(func=query_command)

    # Status command
    status_parser = subparsers.add_parser("status", help="Check system status")
    status_parser.set_defaults(func=status_command)

    return parser


def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    setup_logging(args.verbose if hasattr(args, "verbose") else False)

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except RAGSystemError as e:
        print(f"❌ RAG System Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
