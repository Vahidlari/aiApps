"""This example shows how to use the retriever to search for LaTeX documents.

**Note:** Examples assume Weaviate is running running in DevContainer with Weaviate on the host, update the URL to `http://host.docker.internal:8080`. Alternatively, you may run it natively on your host machine, at `http://host.docker.internal:8080`.
"""

import logging

from ragora import KnowledgeBaseManager

# Configure logging with more detailed formatting
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    kbm = KnowledgeBaseManager(
        url="http://host.docker.internal:8080",  # Weaviate server URL
        grpc_port=50051,  # gRPC port for Weaviate connection
        timeout=30,  # Request timeout in seconds
    )
    kbm.retriever.search_similar("What is the capital of France?")
    print(kbm.retriever.search_similar("What is the capital of France?"))


if __name__ == "__main__":
    main()
