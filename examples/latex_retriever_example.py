"""This example shows how to use the retriever to search for LaTeX documents."""

import logging

from ragnarock import RAGSystem

# Configure logging with more detailed formatting
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


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


def main():
    rag = RAGSystem()
    rag.retriever.search_similar("What is the capital of France?")
    print(rag.retriever.search_similar("What is the capital of France?"))


if __name__ == "__main__":
    main()
