"""Data chunker for RAG system.

This module provides a DataChunker class that can be used to chunk data into
fixed-size segments with overlap.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ChunkMetadata:
    """Metadata for a data chunk in the RAG system.

    This dataclass provides structured metadata for document chunks,
    ensuring type safety and clear field definitions.
    """

    chunk_id: int  # Unique identifier for the chunk
    chunk_size: int  # Size of the chunk in tokens
    total_chunks: int  # Total number of chunks in the document
    source_document: Optional[str] = None  # Source document filename
    page_number: Optional[int] = None  # Page number of the chunk
    section_title: Optional[str] = None  # Section title of the chunk
    chunk_type: Optional[str] = None  # Type of chunk (text, citation, equation, etc.)
    created_at: Optional[str] = None  # Creation date of the chunk


@dataclass
class DataChunk:
    """Data chunk for RAG system.

    This class represents a chunk of data from a document.
    """

    text: str  # The text of the chunk
    start_idx: int  # The start index of the chunk
    end_idx: int  # The end index of the chunk
    metadata: ChunkMetadata  # The metadata of the chunk
    chunk_id: Optional[str] = None  # Unique identifier for the chunk
    source_document: Optional[str] = None  # Source document filename
    chunk_type: Optional[str] = None  # Type of chunk (text, citation, equation, etc.)


class DataChunker:
    """Data chunker for RAG system.

    This class can be used to chunk data into fixed-size segments with overlap.
    """

    def __init__(self, chunk_size: int = 768, overlap_size: int = 100):
        """Initialize the DataChunker.

        Args:
            chunk_size: Size of text chunks in tokens (default: 768)
            overlap_size: Overlap between chunks in tokens (default: 100)
        """
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.chunk_id = 0

    def chunk(
        self,
        text: str,
        chunk_type: str = "text",
        source_document: str = None,
        page_number: int = None,
        section_title: str = None,
        created_at: str = None,
        start_chunk_id: Optional[int] = None,
    ) -> list[DataChunk]:
        """Chunk the text into fixed-size segments with overlap.

        Args:
            text: Text to chunk
            chunk_type: Type of chunk (text, citation, equation, etc.)
            source_document: Source document filename
            page_number: Page number of the chunk
            section_title: Section title of the chunk
            created_at: Creation date of the chunk
            start_chunk_id: Start chunk id
        Returns:
            list[DataChunk]: List of DataChunks
        """
        if not text or not text.strip():
            return []

        # Simple character-based chunking for testing
        # In a real implementation, this would use tokenization
        chunks = []
        start_idx = 0
        if start_chunk_id is not None:
            self.chunk_id = start_chunk_id

        while start_idx < len(text):
            # Calculate end index for this chunk
            end_idx = min(start_idx + self.chunk_size, len(text))

            # Extract chunk text
            chunk_text = text[start_idx:end_idx]

            # Create chunk with metadata
            chunk = DataChunk(
                text=chunk_text,
                start_idx=start_idx,
                end_idx=end_idx,
                metadata=ChunkMetadata(
                    chunk_id=self.chunk_id,
                    chunk_size=len(chunk_text),
                    total_chunks=0,  # Will be updated after all chunks
                    source_document=source_document,
                    page_number=page_number,
                    section_title=section_title,
                    chunk_type=chunk_type,
                    created_at=created_at,
                ),
                chunk_id=str(self.chunk_id),
                chunk_type=chunk_type,
                source_document=source_document,
            )

            chunks.append(chunk)
            self.chunk_id += 1

            # Move start index for next chunk with overlap
            # Ensure we make progress to avoid infinite loop
            if end_idx >= len(text):
                break
            start_idx = max(start_idx + 1, end_idx - self.overlap_size)

        # Update total_chunks in metadata
        for chunk in chunks:
            # Create new metadata with updated total_chunks
            chunk.metadata.total_chunks = len(chunks)

        return chunks
