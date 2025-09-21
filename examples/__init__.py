"""This module contains examples for the RAG system.

Examples include:
- Loading a LaTeX document into the RAG system
- TODO: Loading a PDF document into the RAG system
- TODO: Loading a TXT document into the RAG system

pre-requisites:
- Weaviate running on localhost:8080
- Docker command: docker run -d --name weaviate -p 8080:8080 semitechnologies/weaviate:1.22.4
"""

from . import latex_loading_example, latex_samples, pdf_samples, txt_samples

__all__ = ["latex_samples", "pdf_samples", "txt_samples"]


def main():
    """Main function."""
    latex_loading_example.main()


if __name__ == "__main__":
    main()
