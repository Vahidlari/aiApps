"""This example shows how to use the retriever to search for LaTeX documents.

**Note:** Examples assume Weaviate is running running in DevContainer with Weaviate on the host, update the URL to `http://host.docker.internal:8080`. Alternatively, you may run it natively on your host machine, at `http://host.docker.internal:8080`.
"""

import logging

from ragora import KnowledgeBaseManager, SearchStrategy

# Configure logging with more detailed formatting
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    kbm = KnowledgeBaseManager(
        weaviate_url="http://host.docker.internal:8080",  # Weaviate server URL
    )

    # Search using the new unified API
    result = kbm.search(
        "What is the capital of France?", strategy=SearchStrategy.SIMILAR
    )
    print(f"Query: {result.query}")
    print(f"Strategy: {result.strategy.value}")
    print(f"Found {result.total_found} results in {result.execution_time:.3f}s")

    for i, chunk in enumerate(result.results, 1):
        print(f"{i}. {chunk.get('content', '')[:100]}...")


if __name__ == "__main__":
    main()
