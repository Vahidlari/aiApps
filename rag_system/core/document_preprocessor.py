"""Document preprocessor for LaTeX RAG system.

This module handles the preprocessing pipeline for LaTeX documents before they are used
in the RAG (Retrieval-Augmented Generation) system. It orchestrates the parsing of LaTeX
documents using the LatexParser utility and converts the structured content into
chunked text segments suitable for embedding and vector storage.

Key responsibilities:
- Parse LaTeX documents into structured data (chapters, sections, paragraphs, citations)
- Extract and preserve mathematical equations while cleaning LaTeX formatting
- Process citations and bibliography references with rich metadata
- Chunk documents into fixed-size segments (768 tokens) with overlap (100-150 tokens)
- Prepare clean text content for the embedding engine
- Maintain document structure and citation relationships

The preprocessor returns structured chunks with metadata that can be directly fed to
the embedding engine for vector database storage.
"""

import os

from core.data_chunker import DataChunk, DataChunker
from utils.latex_parser import LatexDocument, LatexParser


class DocumentPreprocessor:
    """Document preprocessor for LaTeX documents in RAG system.

    This class orchestrates the complete preprocessing pipeline for LaTeX documents,
    from parsing to chunking, preparing them for embedding and vector storage.

    Attributes:
        latex_parser: LatexParser instance for document parsing
        chunk_size: Size of text chunks in tokens (default: 768)
        overlap_size: Overlap between chunks in tokens (default: 100-150)
    """

    def __init__(
        self,
        chunker: DataChunker = None,
        chunk_size: int = 768,
        overlap_size: int = 100,
    ):
        """Initialize the DocumentPreprocessor.

        Args:
            chunk_size: Size of text chunks in tokens (default: 768)
            overlap_size: Overlap between chunks in tokens (default: 100-150)
        """
        self.chunker = (
            chunker if chunker is not None else DataChunker(chunk_size, overlap_size)
        )

        self.latex_parser = LatexParser()

    def preprocess_document(self, file_path: str) -> list[DataChunk]:
        """Preprocess the document and return a list of DataChunks.

        Args:
            file_path: Path to the LaTeX document file

        Returns:
            list[DataChunk]: List of DataChunks with metadata
        """
        document = self.latex_parser.parse_document(file_path)

        document_text = self._extract_document_text([document])
        return self.chunker.chunk(document_text)

    def preprocess_documents(self, file_paths: list[str]) -> list[DataChunk]:
        """Preprocess the documents and return a list of DataChunks."""
        documents = [
            self.latex_parser.parse_document(file_path) for file_path in file_paths
        ]
        document_text = self._extract_document_text(documents)
        return self.chunker.chunk(document_text)

    def preprocess_document_folder(self, folder_path: str) -> list[DataChunk]:
        """Preprocess the documents in the folder and return a list of DataChunks."""
        file_paths = [
            os.path.join(folder_path, file) for file in os.listdir(folder_path)
        ]
        return self.preprocess_documents(file_paths)

    def _extract_document_text(self, documentList: list[LatexDocument]) -> str:
        """Extract the text from the document.

        Args:
            documentList: list[LatexDocument]
            Each document in the list is a separate document.

        Returns:
            str: The text from the documents
        """
        content_parts = []

        for document in documentList:
            # Extract from chapters
            if document.chapters:
                for chapter in document.chapters:
                    content_parts.append(f"# {chapter.title}")
                    if chapter.paragraphs:
                        for para in chapter.paragraphs:
                            content_parts.append(para.content)
                    if chapter.sections:
                        for section in chapter.sections:
                            content_parts.append(f"## {section.title}")
                            if section.paragraphs:
                                for para in section.paragraphs:
                                    content_parts.append(para.content)

            # Extract from standalone sections
            if document.sections:
                for section in document.sections:
                    content_parts.append(f"## {section.title}")
                    if section.paragraphs:
                        for para in section.paragraphs:
                            content_parts.append(para.content)

            # Extract from standalone paragraphs
            if document.paragraphs:
                for para in document.paragraphs:
                    content_parts.append(para.content)

            # Extract from tables
            if document.tables:
                for table in document.tables:
                    content_parts.append(table.to_plain_text())

        return "\n\n".join(content_parts)
