"""Utilities for parsing and chunking raw documents prior to ingestion.

The module centralizes the logic for turning LaTeX, Markdown, and text files into
`DataChunk` objects that the rest of the Ragora pipeline can embed and store.
"""

import os

from ..utils.latex_parser import LatexDocument, LatexParser
from ..utils.markdown_parser import MarkdownDocument, MarkdownParser
from .chunking import (
    ChunkingContext,
    ChunkingContextBuilder,
    DataChunk,
    DataChunker,
    DocumentChunkingStrategy,
)


class DocumentPreprocessor:
    """Parse supported file formats into chunkable intermediate data.

    The preprocessor delegates parsing to format-specific helpers and then feeds
    the resulting representation through a :class:`DataChunker`.

    Attributes:
        chunker: Chunking strategy that controls chunk size and overlap.

    Examples:
        ```python
        from ragora.core.document_preprocessor import DocumentPreprocessor

        preprocessor = DocumentPreprocessor()
        chunks = preprocessor.preprocess_document("docs/intro.md", format="markdown")
        ```
    """

    def __init__(self, chunker: DataChunker = None):
        """Initialize the DocumentPreprocessor.

        Args:
            chunker: DataChunker instance (optional)
        """
        if chunker is not None:
            self.chunker = chunker
        else:
            # Create a default document strategy with specified parameters
            self.chunker = DataChunker()
        self.file_extension_map = {
            "latex": [".tex", ".latex", ".bib"],
            "pdf": [".pdf"],
            "docx": [".docx"],
            "doc": [".doc"],
            "markdown": [".md", ".markdown"],
            "text": [".txt"],
            "txt": [".txt"],
        }

        self.latex_parser = LatexParser()
        self.markdown_parser = MarkdownParser()

    def preprocess_document(
        self, file_path: str, format: str = "latex"
    ) -> list[DataChunk]:
        """Preprocess a single document into :class:`DataChunk` objects.

        Args:
            file_path: Path to the document file.
            format: Document format (``"latex"``, ``"markdown"``, or ``"text"``).

        Returns:
            list[DataChunk]: Chunked content ready for embedding downstream.

        Raises:
            ValueError: If an unsupported format is requested.

        Examples:
            ```python
            chunks = preprocessor.preprocess_document("paper.tex", format="latex")
            ```
        """
        normalized_format = format.lower()

        if normalized_format == "latex":
            if file_path.endswith(".bib"):
                self.latex_parser.parse_bibliography(file_path)
                return []
            document = self.latex_parser.parse_document(file_path)
            return self._chunk_documents([document])

        if normalized_format in {"markdown", "md", "text", "txt"}:
            document = self.markdown_parser.parse_document(file_path)
            return self._chunk_markdown_documents([document])

        raise ValueError(f"Unsupported document format: {format}")

    def preprocess_documents(
        self, file_paths: list[str], format: str = "latex"
    ) -> list[DataChunk]:
        """Preprocess multiple documents at once.

        Args:
            file_paths: Collection of paths to document files.
            format: Document format (``"latex"``, ``"markdown"``, or ``"text"``).

        Returns:
            list[DataChunk]: Combined chunks from all input documents.

        Raises:
            ValueError: If an unsupported format is requested.

        Examples:
            ```python
            chunks = preprocessor.preprocess_documents(
                ["chapter1.tex", "chapter2.tex", "references.bib"],
                format="latex",
            )
            ```
        """
        normalized_format = format.lower()

        if normalized_format == "latex":
            # Find the bibliography file
            bibliography_path = None
            for file_path in file_paths:
                if file_path.endswith(".bib"):
                    bibliography_path = file_path
                    break
            if bibliography_path:
                self.latex_parser.parse_bibliography(bibliography_path)
            documents = [
                self.latex_parser.parse_document(file_path)
                for file_path in file_paths
                if file_path != bibliography_path
            ]
            return self._chunk_documents(documents)

        if normalized_format in {"markdown", "md", "text", "txt"}:
            documents = [
                self.markdown_parser.parse_document(path) for path in file_paths
            ]
            return self._chunk_markdown_documents(documents)

        raise ValueError(f"Unsupported document format: {format}")

    def preprocess_document_folder(
        self, folder_path: str, format: str = "latex"
    ) -> list[DataChunk]:
        """Preprocess every supported file in a folder.

        Args:
            folder_path: Directory containing documents that should be ingested.
            format: Document format used to interpret files within the folder.

        Returns:
            list[DataChunk]: Aggregated chunk list for the entire folder.

        Raises:
            ValueError: If ``format`` is not in the supported extension map.
        """
        normalized_format = format.lower()
        if normalized_format not in self.file_extension_map:
            raise ValueError(f"Unsupported document format: {format}")

        file_paths = [
            os.path.join(folder_path, file)
            for file in os.listdir(folder_path)
            if any(
                file.endswith(ext) for ext in self.file_extension_map[normalized_format]
            )
        ]
        return self.preprocess_documents(file_paths, normalized_format)

    def _extract_document_text(self, documentList: list[LatexDocument]) -> str:
        """Merge one or more parsed LaTeX documents into plain text.

        Args:
            documentList: Collection of parsed LaTeX documents to flatten.

        Returns:
            str: Combined Markdown-like text used for chunking.
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

    def _chunk_documents(self, documentList: list[LatexDocument]) -> list[DataChunk]:
        """Chunk multiple LaTeX documents.

        Args:
            documentList: Parsed LaTeX documents.

        Returns:
            list[DataChunk]: Chunked output.
        """
        chunks = []
        if not documentList:
            return chunks
        for document in documentList:
            chunks.extend(self._chunk_document(document))
        return chunks

    def _chunk_markdown_documents(
        self, document_list: list[MarkdownDocument]
    ) -> list[DataChunk]:
        """Chunk Markdown or plain text documents.

        Args:
            document_list: Parsed Markdown documents.

        Returns:
            list[DataChunk]: Chunked output.
        """

        chunks: list[DataChunk] = []
        if not document_list:
            return chunks

        for document in document_list:
            chunks.extend(self._chunk_markdown_document(document))

        return chunks

    def _chunk_markdown_document(self, document: MarkdownDocument) -> list[DataChunk]:
        """Chunk a single Markdown document respecting the original hierarchy.

        Args:
            document: Parsed Markdown document.

        Returns:
            list[DataChunk]: Chunked output.

        Raises:
            ValueError: If ``document`` is ``None``.
        """
        if document is None:
            raise ValueError("Document cannot be None")

        chunk_id_counter = 0
        chunks: list[DataChunk] = []

        if document.paragraphs:
            paragraph_content = "\n\n".join(
                paragraph.content
                for paragraph in document.paragraphs
                if paragraph.content
            )
            if paragraph_content:
                section_label = document.title or document.source_document
                context = (
                    ChunkingContextBuilder()
                    .for_document()
                    .with_source(document.source_document)
                    .with_section(section_label)
                    .with_start_sequence_idx(chunk_id_counter)
                    .build()
                )
                doc_chunks = self.chunker.chunk(paragraph_content, context)
                chunks.extend(doc_chunks)
                chunk_id_counter += len(doc_chunks)

        if document.chapters:
            for chapter in document.chapters:
                chapter_content_parts = [f"# {chapter.title}" if chapter.title else ""]
                chapter_content_parts.extend(
                    paragraph.content
                    for paragraph in chapter.paragraphs
                    if paragraph.content
                )
                chapter_content = "\n\n".join(
                    part for part in chapter_content_parts if part.strip()
                )
                if chapter_content:
                    section_label = (
                        chapter.title or document.title or document.source_document
                    )
                    context = (
                        ChunkingContextBuilder()
                        .for_document()
                        .with_source(document.source_document)
                        .with_section(section_label)
                        .with_start_sequence_idx(chunk_id_counter)
                        .build()
                    )
                    doc_chunks = self.chunker.chunk(chapter_content, context)
                    chunks.extend(doc_chunks)
                    chunk_id_counter += len(doc_chunks)

                if chapter.sections:
                    for section in chapter.sections:
                        section_content_parts = [
                            f"## {section.title}" if section.title else "",
                            *[
                                paragraph.content
                                for paragraph in section.paragraphs
                                if paragraph.content
                            ],
                        ]
                        section_content = "\n\n".join(
                            part for part in section_content_parts if part.strip()
                        )
                        if section_content:
                            section_label = (
                                section.title
                                or chapter.title
                                or document.title
                                or document.source_document
                            )
                            context = (
                                ChunkingContextBuilder()
                                .for_document()
                                .with_source(document.source_document)
                                .with_section(section_label)
                                .with_start_sequence_idx(chunk_id_counter)
                                .build()
                            )
                            doc_chunks = self.chunker.chunk(section_content, context)
                            chunks.extend(doc_chunks)
                            chunk_id_counter += len(doc_chunks)

        if document.sections:
            for section in document.sections:
                section_content_parts = [
                    f"## {section.title}" if section.title else "",
                    *[
                        paragraph.content
                        for paragraph in section.paragraphs
                        if paragraph.content
                    ],
                ]
                section_content = "\n\n".join(
                    part for part in section_content_parts if part.strip()
                )
                if section_content:
                    section_label = (
                        section.title or document.title or document.source_document
                    )
                    context = (
                        ChunkingContextBuilder()
                        .for_document()
                        .with_source(document.source_document)
                        .with_section(section_label)
                        .with_start_sequence_idx(chunk_id_counter)
                        .build()
                    )
                    doc_chunks = self.chunker.chunk(section_content, context)
                    chunks.extend(doc_chunks)
                    chunk_id_counter += len(doc_chunks)

        return chunks

    def _chunk_document(self, document: LatexDocument) -> list[DataChunk]:
        """Chunk the document into a list of DataChunks."""
        if document is None:
            raise ValueError("Document cannot be None")
        chunks = []
        chunk_id_counter = 0

        if document.paragraphs:
            paragraph_content = ""
            for paragraph in document.paragraphs:
                paragraph_content += paragraph.content
            context = (
                ChunkingContextBuilder()
                .for_document()
                .with_source(document.source_document)
                .with_section(document.title)
                .with_start_sequence_idx(chunk_id_counter)
                .build()
            )
            doc_chunks = self.chunker.chunk(paragraph_content, context)
            chunks.extend(doc_chunks)
            chunk_id_counter += len(doc_chunks)

        if document.chapters:
            for chapter in document.chapters:
                chapter_content = f"# {chapter.title}"
                if chapter.paragraphs:
                    for paragraph in chapter.paragraphs:
                        chapter_content += paragraph.content
                    context = (
                        ChunkingContextBuilder()
                        .for_document()
                        .with_source(document.source_document)
                        .with_section(chapter.title)
                        .with_start_sequence_idx(chunk_id_counter)
                        .build()
                    )
                    doc_chunks = self.chunker.chunk(chapter_content, context)
                    chunks.extend(doc_chunks)
                    chunk_id_counter += len(doc_chunks)

                if chapter.sections:
                    for section in chapter.sections:
                        section_content = f"## {section.title}"
                        if section.paragraphs:
                            for paragraph in section.paragraphs:
                                section_content += paragraph.content
                            context = (
                                ChunkingContextBuilder()
                                .for_document()
                                .with_source(document.source_document)
                                .with_section(section.title)
                                .with_start_sequence_idx(chunk_id_counter)
                                .build()
                            )
                            doc_chunks = self.chunker.chunk(section_content, context)
                            chunks.extend(doc_chunks)
                            chunk_id_counter += len(doc_chunks)

        if document.sections:
            for section in document.sections:
                section_content = f"## {section.title}"
                if section.paragraphs:
                    for paragraph in section.paragraphs:
                        section_content += paragraph.content
                    context = (
                        ChunkingContextBuilder()
                        .for_document()
                        .with_source(document.source_document)
                        .with_section(section.title)
                        .with_start_sequence_idx(chunk_id_counter)
                        .build()
                    )
                    doc_chunks = self.chunker.chunk(section_content, context)
                    chunks.extend(doc_chunks)
                    chunk_id_counter += len(doc_chunks)

        if document.tables:
            for table in document.tables:
                table_content = table.to_plain_text()
                context = (
                    ChunkingContextBuilder()
                    .for_document()
                    .with_source(document.source_document)
                    .with_section(document.title)
                    .with_start_sequence_idx(chunk_id_counter)
                    .build()
                )
                doc_chunks = self.chunker.chunk(table_content, context)
                chunks.extend(doc_chunks)
                chunk_id_counter += len(doc_chunks)

        return chunks
