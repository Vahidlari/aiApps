"""This example shows how to use the retriever to search for LaTeX documents."""

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
    kbm = KnowledgeBaseManager()
    kbm.retriever.search_similar("What is the capital of France?")
    print(kbm.retriever.search_similar("What is the capital of France?"))


if __name__ == "__main__":
    main()
