"""Chunking system for Ragora.

This module provides the core chunking functionality for the Ragora system,
including data structures, context management, and the main chunker interface.

## Architecture Overview

The chunking system uses a Strategy Pattern to support different types of content
chunking (text, documents, emails) with a clean, extensible API. The main components are:

- **DataChunker**: Main interface for chunking operations
- **ChunkingContext**: Contains metadata and configuration for chunking
- **ChunkingContextBuilder**: Fluent API for creating contexts
- **ChunkingStrategy**: Abstract base for different chunking implementations
- **DataChunk**: Result object containing chunked text and metadata

## Quick Start

```python
from ragora import DataChunker, ChunkingContextBuilder

# Create a chunker
chunker = DataChunker()

# Basic text chunking
context = ChunkingContextBuilder().for_text().build()
chunks = chunker.chunk("Your text here", context)

# Document chunking with metadata
context = (ChunkingContextBuilder()
          .for_document()
          .with_source("paper.pdf")
          .with_page(1)
          .with_section("Introduction")
          .build())
chunks = chunker.chunk(document_text, context)

# Email chunking
context = (ChunkingContextBuilder()
          .for_email()
          .with_email_info("Meeting Notes", "john@example.com", "team@example.com")
          .build())
chunks = chunker.chunk(email_text, context)
```

## Detailed Usage Guide

### 1. Basic Text Chunking

For simple text chunking without special metadata:

```python
from ragora import DataChunker, ChunkingContextBuilder

chunker = DataChunker()
context = ChunkingContextBuilder().for_text().build()
chunks = chunker.chunk("This is a long text that will be chunked...", context)

# Access chunk data
for chunk in chunks:
    print(f"Chunk {chunk.metadata.chunk_id}: {chunk.text}")
    print(f"Size: {chunk.metadata.chunk_size} characters")
```

### 2. Document Chunking

For academic papers, reports, or structured documents:

```python
context = (ChunkingContextBuilder()
          .for_document()
          .with_source("research_paper.pdf")
          .with_page(5)
          .with_section("Methodology")
          .with_created_at("2024-01-15")
          .build())

chunks = chunker.chunk(document_content, context)

# Document chunks include page and section information
for chunk in chunks:
    print(f"Page {chunk.metadata.page_number}, Section: {chunk.metadata.section_title}")
```

### 3. Email Chunking

For email content with sender/recipient metadata:

```python
context = (ChunkingContextBuilder()
          .for_email()
          .with_email_info(
              subject="Project Update",
              sender="manager@company.com",
              recipient="team@company.com",
              email_id="msg_12345",
              email_date="2024-01-15T14:30:00Z"
          )
          .build())

chunks = chunker.chunk(email_body, context)

# Email chunks preserve sender/recipient information
for chunk in chunks:
    print(f"From: {chunk.metadata.email_sender}")
    print(f"Subject: {chunk.metadata.email_subject}")
```

### 4. Custom Chunking Strategies

Create your own chunking logic for specialized content:

```python
from ragora import ChunkingStrategy, ChunkingContext, DataChunk, ChunkMetadata

class CodeChunkingStrategy(ChunkingStrategy):
    def __init__(self):
        super().__init__(chunk_size=1000, overlap_size=100)

    def chunk(self, text: str, context: ChunkingContext) -> List[DataChunk]:
        # Custom logic for code chunking (e.g., preserve function boundaries)
        # Implementation here...
        pass

# Register and use custom strategy
chunker = DataChunker()
chunker.register_strategy("code", CodeChunkingStrategy())

context = ChunkingContextBuilder().for_text().build()
context.chunk_type = "code"  # Use custom strategy
chunks = chunker.chunk(code_text, context)
```

### 5. Stateless Chunk ID Management

Control chunk ID generation for consistent results:

```python
# Start chunking from ID 100
context = (ChunkingContextBuilder()
          .for_document()
          .with_start_chunk_id(100)
          .build())

chunks = chunker.chunk(text, context)
# First chunk will have ID 100, second chunk ID 101, etc.

# Continue chunking from where you left off
next_context = (ChunkingContextBuilder()
               .for_document()
               .with_start_chunk_id(100 + len(chunks))
               .build())
more_chunks = chunker.chunk(more_text, next_context)
```

### 6. Batch Processing Multiple Documents

Process multiple documents while maintaining unique chunk IDs:

```python
def process_documents(documents):
    chunker = DataChunker()
    all_chunks = []
    chunk_id_counter = 0

    for doc in documents:
        context = (ChunkingContextBuilder()
                  .for_document()
                  .with_source(doc.filename)
                  .with_start_chunk_id(chunk_id_counter)
                  .build())

        chunks = chunker.chunk(doc.content, context)
        all_chunks.extend(chunks)
        chunk_id_counter += len(chunks)

    return all_chunks
```

## Strategy Types and Defaults

| Strategy | Chunk Size | Overlap | Use Case |
|----------|------------|---------|----------|
| TextChunkingStrategy | 768 | 100 | General text content |
| DocumentChunkingStrategy | 768 | 100 | Academic papers, reports |
| EmailChunkingStrategy | 512 | 50 | Email messages |

## Advanced Features

### Custom Metadata

Add custom fields for future extensions:

```python
context = (ChunkingContextBuilder()
          .for_text()
          .with_custom_metadata({
              "language": "en",
              "domain": "scientific",
              "confidence": 0.95
          })
          .build())
```

### Strategy Selection

The chunker automatically selects strategies based on `context.chunk_type`:

```python
# These will use different strategies:
text_context = ChunkingContextBuilder().for_text().build()      # TextChunkingStrategy
doc_context = ChunkingContextBuilder().for_document().build()  # DocumentChunkingStrategy
email_context = ChunkingContextBuilder().for_email().build()  # EmailChunkingStrategy
```

## Performance Considerations

- **Chunk Size**: Larger chunks (768+) work well for documents, smaller (512) for emails
- **Overlap**: Higher overlap (100) preserves context, lower (50) reduces redundancy
- **Memory**: Chunking is memory-efficient, processing text in streams
- **Threading**: Strategies are stateless and thread-safe

## Error Handling

The chunking system handles edge cases gracefully:

```python
# Empty text returns empty list
chunks = chunker.chunk("", context)  # Returns []

# Whitespace-only text returns empty list
chunks = chunker.chunk("   \n\t   ", context)  # Returns []

# Invalid context falls back to default strategy
context.chunk_type = "unknown"
chunks = chunker.chunk(text, context)  # Uses default_strategy
```
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ChunkMetadata:
    """Metadata for a data chunk in Ragora.

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
    email_subject: Optional[str] = None  # Email subject of the chunk
    email_sender: Optional[str] = None  # Email sender of the chunk
    email_recipient: Optional[str] = None  # Email recipient of the chunk
    email_date: Optional[str] = None  # Email date of the chunk
    email_id: Optional[str] = None  # Email id of the chunk
    email_folder: Optional[str] = None  # Email folder of the chunk


@dataclass
class DataChunk:
    """Data chunk for Ragora.

    This class represents a chunk of data from a document.
    """

    text: str  # The text of the chunk
    start_idx: int  # The start index of the chunk
    end_idx: int  # The end index of the chunk
    metadata: ChunkMetadata  # The metadata of the chunk
    source_document: Optional[str] = None  # Source document filename
    chunk_type: Optional[str] = None  # Type of chunk (text, citation, equation, etc.)


@dataclass
class ChunkingContext:
    """Context object containing all chunking metadata and configuration."""

    chunk_type: str = "text"
    source_document: Optional[str] = None
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    created_at: Optional[str] = None
    # Email-specific fields
    email_subject: Optional[str] = None
    email_sender: Optional[str] = None
    email_recipient: Optional[str] = None
    email_date: Optional[str] = None
    email_id: Optional[str] = None
    email_folder: Optional[str] = None
    # Configuration
    start_chunk_id: int = 0
    # Future extensions
    custom_metadata: Optional[Dict[str, Any]] = None


class ChunkingContextBuilder:
    """Builder for creating ChunkingContext objects with fluent API."""

    def __init__(self):
        self._context = ChunkingContext()

    def for_text(self) -> "ChunkingContextBuilder":
        """Set chunk type to text."""
        self._context.chunk_type = "text"
        return self

    def for_document(self) -> "ChunkingContextBuilder":
        """Set chunk type to document."""
        self._context.chunk_type = "document"
        return self

    def for_email(self) -> "ChunkingContextBuilder":
        """Set chunk type to email."""
        self._context.chunk_type = "email"
        return self

    def with_source(self, source: str) -> "ChunkingContextBuilder":
        """Set source document."""
        self._context.source_document = source
        return self

    def with_page(self, page: int) -> "ChunkingContextBuilder":
        """Set page number."""
        self._context.page_number = page
        return self

    def with_section(self, section: str) -> "ChunkingContextBuilder":
        """Set section title."""
        self._context.section_title = section
        return self

    def with_created_at(self, created_at: str) -> "ChunkingContextBuilder":
        """Set creation date."""
        self._context.created_at = created_at
        return self

    def with_email_info(
        self,
        subject: str,
        sender: str,
        recipient: str = None,
        email_id: str = None,
        email_date: str = None,
        email_folder: str = None,
    ) -> "ChunkingContextBuilder":
        """Set email-specific information."""
        self._context.email_subject = subject
        self._context.email_sender = sender
        self._context.email_recipient = recipient
        self._context.email_id = email_id
        self._context.email_date = email_date
        self._context.email_folder = email_folder
        return self

    def with_start_chunk_id(self, chunk_id: int) -> "ChunkingContextBuilder":
        """Set starting chunk ID."""
        self._context.start_chunk_id = chunk_id
        return self

    def with_custom_metadata(
        self, metadata: Dict[str, Any]
    ) -> "ChunkingContextBuilder":
        """Set custom metadata."""
        self._context.custom_metadata = metadata
        return self

    def build(self) -> ChunkingContext:
        """Build the ChunkingContext object."""
        return self._context


class ChunkingStrategy(ABC):
    """Abstract base class for different chunking strategies."""

    def __init__(self, chunk_size: int = 768, overlap_size: int = 100):
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size

    @abstractmethod
    def chunk(self, text: str, context: ChunkingContext) -> List[DataChunk]:
        """Chunk text using the specific strategy."""
        pass


class TextChunkingStrategy(ChunkingStrategy):
    """Standard text chunking strategy."""

    def __init__(self, chunk_size: int = 768, overlap_size: int = 100):
        super().__init__(chunk_size, overlap_size)

    def chunk(self, text: str, context: ChunkingContext) -> List[DataChunk]:
        """Chunk text using standard character-based chunking."""
        return self._chunk_text(text, context)

    def _chunk_text(self, text: str, context: ChunkingContext) -> List[DataChunk]:
        """Core chunking logic."""
        if not text or not text.strip():
            return []

        chunks = []
        start_idx = 0
        chunk_id = context.start_chunk_id

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
                    chunk_id=chunk_id,
                    chunk_size=len(chunk_text),
                    total_chunks=0,  # Will be updated after all chunks
                    source_document=context.source_document,
                    page_number=context.page_number,
                    section_title=context.section_title,
                    chunk_type=context.chunk_type,
                    created_at=context.created_at,
                    email_subject=context.email_subject,
                    email_sender=context.email_sender,
                    email_recipient=context.email_recipient,
                    email_date=context.email_date,
                    email_id=context.email_id,
                    email_folder=context.email_folder,
                ),
                chunk_type=context.chunk_type,
                source_document=context.source_document,
            )

            chunks.append(chunk)
            chunk_id += 1

            # Move start index for next chunk with overlap
            # Ensure we make progress to avoid infinite loop
            if end_idx >= len(text):
                break
            start_idx = max(start_idx + 1, end_idx - self.overlap_size)

        # Update total_chunks in metadata
        for chunk in chunks:
            chunk.metadata.total_chunks = len(chunks)

        return chunks


class DocumentChunkingStrategy(ChunkingStrategy):
    """Document-specific chunking strategy."""

    def __init__(self, chunk_size: int = 768, overlap_size: int = 100):
        super().__init__(chunk_size, overlap_size)

    def chunk(self, text: str, context: ChunkingContext) -> List[DataChunk]:
        """Chunk text using document-aware chunking."""
        # For now, use the same logic as text chunking
        # Future: could implement section-aware chunking, citation preservation, etc.
        return self._chunk_text(text, context)

    def _chunk_text(self, text: str, context: ChunkingContext) -> List[DataChunk]:
        """Core chunking logic (same as TextChunkingStrategy for now)."""
        if not text or not text.strip():
            return []

        chunks = []
        start_idx = 0
        chunk_id = context.start_chunk_id

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
                    chunk_id=chunk_id,
                    chunk_size=len(chunk_text),
                    total_chunks=0,  # Will be updated after all chunks
                    source_document=context.source_document,
                    page_number=context.page_number,
                    section_title=context.section_title,
                    chunk_type=context.chunk_type,
                    created_at=context.created_at,
                    email_subject=context.email_subject,
                    email_sender=context.email_sender,
                    email_recipient=context.email_recipient,
                    email_date=context.email_date,
                    email_id=context.email_id,
                    email_folder=context.email_folder,
                ),
                chunk_type=context.chunk_type,
                source_document=context.source_document,
            )

            chunks.append(chunk)
            chunk_id += 1

            # Move start index for next chunk with overlap
            # Ensure we make progress to avoid infinite loop
            if end_idx >= len(text):
                break
            start_idx = max(start_idx + 1, end_idx - self.overlap_size)

        # Update total_chunks in metadata
        for chunk in chunks:
            chunk.metadata.total_chunks = len(chunks)

        return chunks


class EmailChunkingStrategy(ChunkingStrategy):
    """Email-specific chunking strategy."""

    def __init__(self, chunk_size: int = 512, overlap_size: int = 50):
        super().__init__(chunk_size, overlap_size)

    def chunk(self, text: str, context: ChunkingContext) -> List[DataChunk]:
        """Chunk text using email-aware chunking."""
        # For now, use the same logic as text chunking
        # Future: could implement thread-aware chunking, attachment handling, etc.
        return self._chunk_text(text, context)

    def _chunk_text(self, text: str, context: ChunkingContext) -> List[DataChunk]:
        """Core chunking logic (same as TextChunkingStrategy for now)."""
        if not text or not text.strip():
            return []

        chunks = []
        start_idx = 0
        chunk_id = context.start_chunk_id

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
                    chunk_id=chunk_id,
                    chunk_size=len(chunk_text),
                    total_chunks=0,  # Will be updated after all chunks
                    source_document=context.source_document,
                    page_number=context.page_number,
                    section_title=context.section_title,
                    chunk_type=context.chunk_type,
                    created_at=context.created_at,
                    email_subject=context.email_subject,
                    email_sender=context.email_sender,
                    email_recipient=context.email_recipient,
                    email_date=context.email_date,
                    email_id=context.email_id,
                    email_folder=context.email_folder,
                ),
                chunk_type=context.chunk_type,
                source_document=context.source_document,
            )

            chunks.append(chunk)
            chunk_id += 1

            # Move start index for next chunk with overlap
            # Ensure we make progress to avoid infinite loop
            if end_idx >= len(text):
                break
            start_idx = max(start_idx + 1, end_idx - self.overlap_size)

        # Update total_chunks in metadata
        for chunk in chunks:
            chunk.metadata.total_chunks = len(chunks)

        return chunks


class DataChunker:
    """Data chunker for RAG system using strategy pattern.

    This class delegates chunking to appropriate strategies based on context.
    """

    def __init__(self, default_strategy: ChunkingStrategy = None):
        """Initialize the DataChunker with default strategies.

        Args:
            default_strategy: Default strategy to use when no specific strategy is registered
        """
        self.default_strategy = default_strategy or TextChunkingStrategy()
        self.strategies: Dict[str, ChunkingStrategy] = {
            "text": TextChunkingStrategy(),
            "document": DocumentChunkingStrategy(),
            "email": EmailChunkingStrategy(),
        }

    def chunk(self, text: str, context: ChunkingContext) -> List[DataChunk]:
        """Chunk text using the appropriate strategy based on context.

        Args:
            text: Text to chunk
            context: ChunkingContext containing metadata and configuration

        Returns:
            List[DataChunk]: List of DataChunks
        """
        strategy = self.strategies.get(context.chunk_type, self.default_strategy)
        return strategy.chunk(text, context)

    def register_strategy(self, chunk_type: str, strategy: ChunkingStrategy):
        """Register a new chunking strategy.

        Args:
            chunk_type: Type identifier for the strategy
            strategy: ChunkingStrategy implementation
        """
        self.strategies[chunk_type] = strategy
