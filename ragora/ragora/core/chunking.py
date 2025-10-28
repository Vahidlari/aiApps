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
# Start chunking from sequence index 100
context = (ChunkingContextBuilder()
          .for_document()
          .with_start_sequence_idx(100)
          .build())

chunks = chunker.chunk(text, context)
# First chunk will have sequence number 100, second chunk 101, etc.

# Continue chunking from where you left off
next_context = (ChunkingContextBuilder()
               .for_document()
               .with_start_sequence_idx(100 + len(chunks))
               .build())
more_chunks = chunker.chunk(more_text, next_context)
```

### 6. Batch Processing Multiple Documents

Process multiple documents while maintaining unique chunk IDs:

```python
def process_documents(documents):
    chunker = DataChunker()
    all_chunks = []
    sequence_idx_counter = 0

    for doc in documents:
        context = (ChunkingContextBuilder()
                  .for_document()
                  .with_source(doc.filename)
                  .with_start_sequence_idx(sequence_idx_counter)
                  .build())

        chunks = chunker.chunk(doc.content, context)
        all_chunks.extend(chunks)
        sequence_idx_counter += len(chunks)

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

import hashlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


class ChunkIdGenerator:
    """Centralized, deterministic chunk ID generator for all chunking strategies.

    This class provides a unified way to generate human-readable, deterministic
    chunk IDs across all content types and chunking strategies. The IDs follow
    a composite format that includes content type, source identification,
    location information, and sequence numbering.

    ID Format: {content_type}:{source_id}:{location_id}:{sequence_id}

    Examples:
    - text:doc_001:0:0001
    - document:paper_2024_01:page_5:0003
    - email:msg_abc123:thread_001:0001
    - custom:user_data:batch_001:0002
    """

    @staticmethod
    def generate_chunk_id(
        content_type: str,
        source_id: str,
        location_id: str = "0",
        sequence_id: int = 0,
        chunk_idx: int = 0,
    ) -> str:
        """Generate a deterministic, human-readable chunk ID.

        Args:
            content_type: Type of content (text, document, email, custom)
            source_id: Unique identifier for the source document/content
            location_id: Location within source (page, section, etc.)
            sequence_id: Starting sequence number for this chunking session
            chunk_idx: Index of this chunk within the sequence

        Returns:
            str: Deterministic chunk ID in format
                 content_type:source_id:location_id:sequence_num
        """
        # Normalize inputs
        content_type = ChunkIdGenerator._normalize_content_type(content_type)
        source_id = ChunkIdGenerator._normalize_source_id(source_id)
        location_id = ChunkIdGenerator._normalize_location_id(location_id)

        # Generate sequence number
        sequence_num = sequence_id + chunk_idx

        return f"{content_type}:{source_id}:{location_id}:{sequence_num:04d}"

    @staticmethod
    def _normalize_content_type(content_type: str) -> str:
        """Normalize content type for consistent formatting."""
        if not content_type:
            return "text"

        # Convert to lowercase and validate
        normalized = content_type.lower().strip()

        # Map common variations to standard types
        type_mapping = {
            "doc": "document",
            "docs": "document",
            "msg": "email",
            "mail": "email",
            "txt": "text",
            "plain": "text",
        }

        return type_mapping.get(normalized, normalized)

    @staticmethod
    def _normalize_source_id(source_id: str) -> str:
        """Normalize source ID for consistent formatting."""
        if not source_id:
            return "unknown"

        # Remove special characters, convert to lowercase, limit length
        normalized = re.sub(r"[^a-zA-Z0-9_-]", "_", source_id.lower())
        normalized = re.sub(r"_+", "_", normalized)  # Collapse multiple underscores
        normalized = normalized.strip("_")  # Remove leading/trailing underscores

        return normalized[:20] if normalized else "unknown"  # Limit to 20 chars

    @staticmethod
    def _normalize_location_id(location_id: str) -> str:
        """Normalize location ID for consistent formatting."""
        if not location_id:
            return "0"

        # Convert to string and normalize
        location_str = str(location_id).lower().strip()

        # Handle common location patterns
        if location_str == "0":
            return "0"  # Keep "0" as is for default case
        elif location_str.isdigit():
            return f"pos_{location_str}"
        elif location_str.startswith("page_"):
            return location_str
        elif location_str.startswith("sec_"):
            return location_str
        elif location_str.startswith("msg_"):
            return location_str
        else:
            # General normalization
            normalized = re.sub(r"[^a-zA-Z0-9_-]", "_", location_str)
            normalized = re.sub(r"_+", "_", normalized)
            normalized = normalized.strip("_")
            return normalized[:15] if normalized else "0"  # Limit to 15 chars

    @staticmethod
    def parse_chunk_id(chunk_id: str) -> Dict[str, str]:
        """Parse a chunk ID back into its components.

        Args:
            chunk_id: The chunk ID to parse

        Returns:
            Dict containing parsed components: content_type, source_id, location_id, sequence_num

        Raises:
            ValueError: If chunk ID format is invalid
        """
        parts = chunk_id.split(":")
        if len(parts) != 4:
            raise ValueError(
                f"Invalid chunk ID format: {chunk_id}. Expected format: content_type:source_id:location_id:sequence_num"
            )

        return {
            "content_type": parts[0],
            "source_id": parts[1],
            "location_id": parts[2],
            "sequence_num": parts[3],
        }

    @staticmethod
    def get_source_hash(source_id: str, max_length: int = 8) -> str:
        """Generate a short hash for source ID when it's too long.

        Args:
            source_id: The source ID to hash
            max_length: Maximum length of the hash

        Returns:
            str: Short hash of the source ID
        """
        if not source_id:
            return "unknown"

        # Create a deterministic hash
        hash_obj = hashlib.md5(source_id.encode("utf-8"))
        hash_hex = hash_obj.hexdigest()

        return hash_hex[:max_length]


@dataclass
class ChunkMetadata:
    """Metadata for a data chunk in Ragora.

    This dataclass provides structured metadata for document chunks,
    ensuring type safety and clear field definitions.
    """

    chunk_idx: int  # Index of the chunk in the document
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
    custom_metadata: Optional[Dict[str, Any]] = None  # Custom metadata dictionary


@dataclass
class DataChunk:
    """Data chunk for Ragora.

    This class represents a chunk of data from a document.
    """

    text: str  # The text of the chunk
    start_idx: int  # The start index of the chunk
    end_idx: int  # The end index of the chunk
    chunk_id: str  # The deterministic human-readable chunk ID
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
    # ID generation parameters
    source_id: Optional[str] = None  # Unique source identifier for ID generation
    location_id: Optional[str] = None  # Location within source (page, section, etc.)
    start_sequence_idx: int = 0  # Starting sequence index for deterministic IDs
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

    def with_source_id(self, source_id: str) -> "ChunkingContextBuilder":
        """Set unique source identifier for deterministic ID generation."""
        self._context.source_id = source_id
        return self

    def with_location_id(self, location_id: str) -> "ChunkingContextBuilder":
        """Set location within source for deterministic ID generation."""
        self._context.location_id = location_id
        return self

    def with_start_sequence_idx(self, sequence_idx: int) -> "ChunkingContextBuilder":
        """Set starting sequence index for deterministic ID generation."""
        self._context.start_sequence_idx = sequence_idx
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

    # Convenience methods for common patterns
    def for_document_with_page(
        self, source_id: str, page: int
    ) -> "ChunkingContextBuilder":
        """Set up for document chunking with page number and source ID."""
        return (
            self.for_document()
            .with_source_id(source_id)
            .with_page(page)
            .with_location_id(f"page_{page}")
        )

    def for_email_with_id(
        self, email_id: str, subject: str, sender: str
    ) -> "ChunkingContextBuilder":
        """Set up for email chunking with email ID and metadata."""
        return (
            self.for_email()
            .with_source_id(f"email_{email_id}")
            .with_email_info(subject, sender)
            .with_location_id(f"msg_{email_id}")
        )

    def for_text_with_source(self, source_id: str) -> "ChunkingContextBuilder":
        """Set up for text chunking with source ID."""
        return self.for_text().with_source_id(source_id)


class ChunkingStrategy(ABC):
    """Abstract base class for different chunking strategies."""

    def __init__(self, chunk_size: int = 768, overlap_size: int = 100):
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size

    @abstractmethod
    def chunk(self, text: str, context: ChunkingContext) -> List[DataChunk]:
        """Chunk text using the specific strategy."""
        pass

    def _create_chunk_with_id(
        self,
        text: str,
        start_idx: int,
        end_idx: int,
        chunk_idx: int,
        context: ChunkingContext,
    ) -> DataChunk:
        """Create a DataChunk with deterministic ID generation.

        Args:
            text: The chunk text content
            start_idx: Start index in original text
            end_idx: End index in original text
            chunk_idx: Index of this chunk in the sequence
            context: Chunking context with metadata

        Returns:
            DataChunk with deterministic chunk_id
        """
        # Generate deterministic chunk ID
        chunk_id = ChunkIdGenerator.generate_chunk_id(
            content_type=context.chunk_type,
            source_id=self._get_source_id(context),
            location_id=self._get_location_id(context),
            sequence_id=context.start_sequence_idx,
            chunk_idx=chunk_idx,
        )

        return DataChunk(
            text=text,
            start_idx=start_idx,
            end_idx=end_idx,
            chunk_id=chunk_id,
            metadata=ChunkMetadata(
                chunk_idx=chunk_idx,
                chunk_size=len(text),
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
                custom_metadata=context.custom_metadata,
            ),
            chunk_type=context.chunk_type,
            source_document=context.source_document,
        )

    def _get_source_id(self, context: ChunkingContext) -> str:
        """Get source ID for chunk ID generation."""
        if context.source_id:
            return context.source_id
        elif context.source_document:
            return context.source_document
        elif context.email_id:
            return f"email_{context.email_id}"
        else:
            return "unknown"

    def _get_location_id(self, context: ChunkingContext) -> str:
        """Get location ID for chunk ID generation."""
        if context.location_id:
            return context.location_id
        elif context.chunk_type == "document" and context.page_number:
            return f"page_{context.page_number}"
        elif context.chunk_type == "email" and context.email_id:
            return f"msg_{context.email_id}"
        elif context.section_title:
            return f"sec_{context.section_title[:10]}"
        else:
            return "0"


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
        chunk_idx = 0  # Start at 0, sequence_id is handled in ID generation

        while start_idx < len(text):
            # Calculate end index for this chunk
            end_idx = min(start_idx + self.chunk_size, len(text))

            # Extract chunk text
            chunk_text = text[start_idx:end_idx]

            # Create chunk with deterministic ID
            chunk = self._create_chunk_with_id(
                text=chunk_text,
                start_idx=start_idx,
                end_idx=end_idx,
                chunk_idx=chunk_idx,
                context=context,
            )

            chunks.append(chunk)
            chunk_idx += 1

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
        chunk_idx = 0  # Start at 0, sequence_id is handled in ID generation

        while start_idx < len(text):
            # Calculate end index for this chunk
            end_idx = min(start_idx + self.chunk_size, len(text))

            # Extract chunk text
            chunk_text = text[start_idx:end_idx]

            # Create chunk with deterministic ID
            chunk = self._create_chunk_with_id(
                text=chunk_text,
                start_idx=start_idx,
                end_idx=end_idx,
                chunk_idx=chunk_idx,
                context=context,
            )

            chunks.append(chunk)
            chunk_idx += 1

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
        chunk_idx = 0  # Start at 0, sequence_id is handled in ID generation

        while start_idx < len(text):
            # Calculate end index for this chunk
            end_idx = min(start_idx + self.chunk_size, len(text))

            # Extract chunk text
            chunk_text = text[start_idx:end_idx]

            # Create chunk with deterministic ID
            chunk = self._create_chunk_with_id(
                text=chunk_text,
                start_idx=start_idx,
                end_idx=end_idx,
                chunk_idx=chunk_idx,
                context=context,
            )

            chunks.append(chunk)
            chunk_idx += 1

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
