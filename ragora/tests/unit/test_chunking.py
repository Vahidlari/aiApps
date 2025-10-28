"""
Unit tests for chunking system in the RAG system.
"""

from typing import List

from ragora import (
    ChunkingContext,
    ChunkingContextBuilder,
    ChunkingStrategy,
    ChunkMetadata,
    DataChunk,
    DataChunker,
    DocumentChunkingStrategy,
    EmailChunkingStrategy,
    TextChunkingStrategy,
)


class TestChunkingContext:
    """Test ChunkingContext dataclass."""

    def test_chunking_context_creation(self):
        """Test basic ChunkingContext object creation."""
        context = ChunkingContext()
        assert context.chunk_type == "text"
        assert context.source_document is None
        assert context.start_sequence_idx == 0

    def test_chunking_context_with_values(self):
        """Test ChunkingContext creation with values."""
        context = ChunkingContext(
            chunk_type="document",
            source_document="test.pdf",
            page_number=1,
            section_title="Introduction",
            start_sequence_idx=100,
        )
        assert context.chunk_type == "document"
        assert context.source_document == "test.pdf"
        assert context.page_number == 1
        assert context.section_title == "Introduction"
        assert context.start_sequence_idx == 100

    def test_chunking_context_email_fields(self):
        """Test ChunkingContext with email fields."""
        context = ChunkingContext(
            chunk_type="email",
            email_subject="Test Email",
            email_sender="sender@example.com",
            email_recipient="recipient@example.com",
            email_id="msg123",
            email_date="2024-01-01T10:00:00Z",
        )
        assert context.chunk_type == "email"
        assert context.email_subject == "Test Email"
        assert context.email_sender == "sender@example.com"
        assert context.email_recipient == "recipient@example.com"
        assert context.email_id == "msg123"
        assert context.email_date == "2024-01-01T10:00:00Z"


class TestChunkingContextBuilder:
    """Test ChunkingContextBuilder class."""

    def test_builder_basic_usage(self):
        """Test basic builder usage."""
        context = (
            ChunkingContextBuilder()
            .for_document()
            .with_source("test.pdf")
            .with_page(1)
            .build()
        )

        assert context.chunk_type == "document"
        assert context.source_document == "test.pdf"
        assert context.page_number == 1

    def test_builder_email_usage(self):
        """Test builder with email information."""
        context = (
            ChunkingContextBuilder()
            .for_email()
            .with_email_info(
                "Test Subject", "sender@example.com", "recipient@example.com"
            )
            .with_start_sequence_idx(50)
            .build()
        )

        assert context.chunk_type == "email"
        assert context.email_subject == "Test Subject"
        assert context.email_sender == "sender@example.com"
        assert context.email_recipient == "recipient@example.com"
        assert context.start_sequence_idx == 50

    def test_builder_fluent_api(self):
        """Test builder fluent API chaining."""
        context = (
            ChunkingContextBuilder()
            .for_text()
            .with_source("document.txt")
            .with_section("Chapter 1")
            .with_created_at("2024-01-01")
            .with_start_sequence_idx(10)
            .build()
        )

        assert context.chunk_type == "text"
        assert context.source_document == "document.txt"
        assert context.section_title == "Chapter 1"
        assert context.created_at == "2024-01-01"
        assert context.start_sequence_idx == 10


class TestChunkingStrategies:
    """Test chunking strategy classes."""

    def test_text_chunking_strategy(self):
        """Test TextChunkingStrategy."""
        strategy = TextChunkingStrategy(chunk_size=10, overlap_size=2)
        context = ChunkingContext(chunk_type="text", start_sequence_idx=0)
        text = "1234567890abcdefghij"

        chunks = strategy.chunk(text, context)

        assert len(chunks) == 3
        assert chunks[0].text == "1234567890"
        assert chunks[0].chunk_id == "text:unknown:0:0000"
        assert chunks[1].text == "90abcdefgh"
        assert chunks[1].chunk_id == "text:unknown:0:0001"
        assert chunks[2].text == "ghij"  # Updated expectation
        assert chunks[2].chunk_id == "text:unknown:0:0002"

    def test_document_chunking_strategy(self):
        """Test DocumentChunkingStrategy."""
        strategy = DocumentChunkingStrategy(chunk_size=5, overlap_size=1)
        context = ChunkingContext(chunk_type="document", start_sequence_idx=10)
        text = "1234567890"

        chunks = strategy.chunk(text, context)

        assert len(chunks) == 3
        assert chunks[0].chunk_id == "document:unknown:0:0010"
        assert chunks[1].chunk_id == "document:unknown:0:0011"
        assert chunks[2].chunk_id == "document:unknown:0:0012"

    def test_email_chunking_strategy(self):
        """Test EmailChunkingStrategy."""
        strategy = EmailChunkingStrategy(chunk_size=8, overlap_size=2)
        context = ChunkingContext(chunk_type="email", start_sequence_idx=5)
        text = "1234567890abcdefgh"

        chunks = strategy.chunk(text, context)

        assert len(chunks) == 3
        assert chunks[0].chunk_id == "email:unknown:0:0005"
        assert chunks[1].chunk_id == "email:unknown:0:0006"
        assert chunks[2].chunk_id == "email:unknown:0:0007"


class TestDataChunk:
    """Test DataChunk dataclass."""

    def test_data_chunk_creation(self):
        """Test basic DataChunk object creation."""
        metadata = ChunkMetadata(chunk_idx=0, chunk_size=18, total_chunks=1)
        chunk = DataChunk(
            text="This is a test chunk",
            start_idx=0,
            end_idx=18,
            chunk_id="test_chunk_001",
            metadata=metadata,
        )

        assert chunk.text == "This is a test chunk"
        assert chunk.start_idx == 0
        assert chunk.end_idx == 18
        assert chunk.chunk_id == "test_chunk_001"
        assert chunk.metadata.chunk_size == 18

    def test_data_chunk_with_empty_text(self):
        """Test DataChunk creation with empty text."""
        metadata = ChunkMetadata(chunk_idx=0, chunk_size=0, total_chunks=1)
        chunk = DataChunk(
            text="", start_idx=0, end_idx=0, chunk_id="empty_chunk", metadata=metadata
        )

        assert chunk.text == ""
        assert chunk.start_idx == 0
        assert chunk.end_idx == 0
        assert chunk.metadata.chunk_size == 0

    def test_data_chunk_with_complex_metadata(self):
        """Test DataChunk creation with complex metadata."""
        metadata = ChunkMetadata(
            chunk_idx=5,
            chunk_size=100,
            total_chunks=10,
            source_document="doc123",
            section_title="introduction",
        )

        chunk = DataChunk(
            text="Complex chunk with metadata",
            start_idx=500,
            end_idx=600,
            chunk_id="complex_chunk_005",
            metadata=metadata,
        )

        assert chunk.chunk_id == "complex_chunk_005"
        assert chunk.metadata.chunk_size == 100
        assert chunk.metadata.total_chunks == 10
        assert chunk.metadata.source_document == "doc123"
        assert chunk.metadata.section_title == "introduction"


class TestDataChunker:
    """Test DataChunker class."""

    def test_data_chunker_default_initialization(self):
        """Test DataChunker initialization with default parameters."""
        chunker = DataChunker()

        assert chunker.default_strategy is not None
        assert "text" in chunker.strategies
        assert "document" in chunker.strategies
        assert "email" in chunker.strategies

    def test_data_chunker_custom_strategy(self):
        """Test DataChunker with custom default strategy."""
        custom_strategy = TextChunkingStrategy(chunk_size=512, overlap_size=50)
        chunker = DataChunker(default_strategy=custom_strategy)

        assert chunker.default_strategy == custom_strategy

    def test_chunk_empty_text(self):
        """Test chunking empty text."""
        chunker = DataChunker()
        context = ChunkingContext()

        result = chunker.chunk("", context)
        assert result == []

        result = chunker.chunk("   ", context)
        assert result == []

    def test_chunk_whitespace_only_text(self):
        """Test chunking whitespace-only text."""
        chunker = DataChunker()
        context = ChunkingContext()

        result = chunker.chunk("   \n\t   ", context)
        assert result == []

    def test_chunk_single_character(self):
        """Test chunking single character text."""
        chunker = DataChunker()
        context = ChunkingContext(chunk_type="text", start_sequence_idx=0)

        result = chunker.chunk("a", context)

        assert len(result) == 1
        assert result[0].text == "a"
        assert result[0].start_idx == 0
        assert result[0].end_idx == 1
        assert result[0].chunk_id == "text:unknown:0:0000"
        assert result[0].metadata.chunk_size == 1
        assert result[0].metadata.total_chunks == 1

    def test_chunk_small_text_no_overlap_needed(self):
        """Test chunking small text that fits in one chunk."""
        chunker = DataChunker()
        context = ChunkingContext(chunk_type="text", start_sequence_idx=0)
        text = "This is a small text that fits in one chunk."

        result = chunker.chunk(text, context)

        assert len(result) == 1
        assert result[0].text == text
        assert result[0].start_idx == 0
        assert result[0].end_idx == len(text)
        assert result[0].chunk_id == "text:unknown:0:0000"
        assert result[0].metadata.chunk_size == len(text)
        assert result[0].metadata.total_chunks == 1

    def test_chunk_text_requires_multiple_chunks(self):
        """Test chunking text that requires multiple chunks."""
        chunker = DataChunker()
        context = ChunkingContext(chunk_type="text", start_sequence_idx=0)
        text = "1234567890"  # 10 characters, should create multiple chunks with default size

        result = chunker.chunk(text, context)

        assert len(result) >= 1
        # Verify chunk_id sequence
        for i, chunk in enumerate(result):
            assert chunk.chunk_id == f"text:unknown:0:{i:04d}"

    def test_chunk_with_different_strategies(self):
        """Test chunking with different strategy types."""
        chunker = DataChunker()
        text = "1234567890abcdefghij"

        # Test text strategy
        text_context = ChunkingContext(chunk_type="text", start_sequence_idx=0)
        text_chunks = chunker.chunk(text, text_context)

        # Test document strategy
        doc_context = ChunkingContext(chunk_type="document", start_sequence_idx=0)
        doc_chunks = chunker.chunk(text, doc_context)

        # Test email strategy
        email_context = ChunkingContext(chunk_type="email", start_sequence_idx=0)
        email_chunks = chunker.chunk(text, email_context)

        # All should produce chunks (may be different due to different chunk sizes)
        assert len(text_chunks) >= 1
        assert len(doc_chunks) >= 1
        assert len(email_chunks) >= 1

    def test_chunk_with_custom_start_id(self):
        """Test chunking with custom start chunk ID."""
        chunker = DataChunker()
        context = ChunkingContext(chunk_type="text", start_sequence_idx=100)
        text = "1234567890"

        result = chunker.chunk(text, context)

        assert len(result) >= 1
        # Verify chunk_id starts at 100
        for i, chunk in enumerate(result):
            assert chunk.chunk_id == f"text:unknown:0:{100 + i:04d}"

    def test_chunk_with_metadata(self):
        """Test chunking with metadata."""
        chunker = DataChunker()
        context = ChunkingContext(
            chunk_type="document",
            source_document="test.pdf",
            page_number=1,
            section_title="Introduction",
            start_sequence_idx=0,
        )
        text = "This is a test document."

        result = chunker.chunk(text, context)

        assert len(result) >= 1
        for chunk in result:
            assert chunk.metadata.source_document == "test.pdf"
            assert chunk.metadata.page_number == 1
            assert chunk.metadata.section_title == "Introduction"
            assert chunk.metadata.chunk_type == "document"

    def test_chunk_with_email_metadata(self):
        """Test chunking with email metadata."""
        chunker = DataChunker()
        context = ChunkingContext(
            chunk_type="email",
            email_subject="Test Email",
            email_sender="sender@example.com",
            email_recipient="recipient@example.com",
            email_id="msg123",
            email_date="2024-01-01T10:00:00Z",
            start_sequence_idx=0,
        )
        text = "This is a test email."

        result = chunker.chunk(text, context)

        assert len(result) >= 1
        for chunk in result:
            assert chunk.metadata.email_subject == "Test Email"
            assert chunk.metadata.email_sender == "sender@example.com"
            assert chunk.metadata.email_recipient == "recipient@example.com"
            assert chunk.metadata.email_id == "msg123"
            assert chunk.metadata.email_date == "2024-01-01T10:00:00Z"

    def test_chunk_with_custom_metadata(self):
        """Test chunking with custom metadata."""
        chunker = DataChunker()
        context = ChunkingContext(
            chunk_type="document",
            source_document="test.pdf",
            page_number=1,
            section_title="Introduction",
            start_sequence_idx=0,
            custom_metadata={
                "language": "en",
                "domain": "scientific",
                "confidence": 0.95,
                "tags": ["physics", "relativity"],
                "priority": 5,
                "content_category": "research_paper",
                "author": "Einstein",
                "year": 1905,
            },
        )
        text = "This is a scientific document about relativity."

        result = chunker.chunk(text, context)

        assert len(result) >= 1
        for chunk in result:
            assert chunk.metadata.custom_metadata is not None
            assert chunk.metadata.custom_metadata["language"] == "en"
            assert chunk.metadata.custom_metadata["domain"] == "scientific"
            assert chunk.metadata.custom_metadata["confidence"] == 0.95
            assert chunk.metadata.custom_metadata["tags"] == ["physics", "relativity"]
            assert chunk.metadata.custom_metadata["priority"] == 5
            assert (
                chunk.metadata.custom_metadata["content_category"] == "research_paper"
            )
            assert chunk.metadata.custom_metadata["author"] == "Einstein"
            assert chunk.metadata.custom_metadata["year"] == 1905

    def test_register_custom_strategy(self):
        """Test registering a custom strategy."""
        chunker = DataChunker()

        # Create a custom strategy
        class CustomStrategy(ChunkingStrategy):
            def chunk(self, text: str, context: ChunkingContext) -> List[DataChunk]:
                # Simple strategy that creates one chunk per character
                chunks = []
                for i, char in enumerate(text):
                    chunk = DataChunk(
                        text=char,
                        start_idx=i,
                        end_idx=i + 1,
                        metadata=ChunkMetadata(
                            chunk_idx=context.start_sequence_idx + i,
                            chunk_size=1,
                            total_chunks=len(text),
                            chunk_type=context.chunk_type,
                        ),
                        chunk_id=f"custom:unknown:0:{context.start_sequence_idx + i:04d}",
                        chunk_type=context.chunk_type,
                    )
                    chunks.append(chunk)
                return chunks

        # Register the custom strategy
        chunker.register_strategy("custom", CustomStrategy())

        # Test using the custom strategy
        context = ChunkingContext(chunk_type="custom", start_sequence_idx=0)
        text = "abc"
        result = chunker.chunk(text, context)

        assert len(result) == 3
        assert result[0].text == "a"
        assert result[1].text == "b"
        assert result[2].text == "c"

    def test_strategy_fallback_to_default(self):
        """Test that unknown strategy types fall back to default strategy."""
        chunker = DataChunker()
        context = ChunkingContext(chunk_type="unknown_type", start_sequence_idx=0)
        text = "test"

        result = chunker.chunk(text, context)

        # Should still work with default strategy
        assert len(result) >= 1
        for chunk in result:
            assert chunk.metadata.chunk_type == "unknown_type"
