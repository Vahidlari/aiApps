"""
Unit tests for DataChunker class in the RAG system.
"""

from ragnarock import ChunkMetadata, DataChunk, DataChunker


class TestDataChunk:
    """Test DataChunk dataclass."""

    def test_data_chunk_creation(self):
        """Test basic DataChunk object creation."""
        metadata = ChunkMetadata(chunk_id=0, chunk_size=18, total_chunks=1)
        chunk = DataChunk(
            text="This is a test chunk",
            start_idx=0,
            end_idx=18,
            metadata=metadata,
        )

        assert chunk.text == "This is a test chunk"
        assert chunk.start_idx == 0
        assert chunk.end_idx == 18
        assert chunk.metadata.chunk_id == 0
        assert chunk.metadata.chunk_size == 18

    def test_data_chunk_with_empty_text(self):
        """Test DataChunk creation with empty text."""
        metadata = ChunkMetadata(chunk_id=0, chunk_size=0, total_chunks=1)
        chunk = DataChunk(text="", start_idx=0, end_idx=0, metadata=metadata)

        assert chunk.text == ""
        assert chunk.start_idx == 0
        assert chunk.end_idx == 0
        assert chunk.metadata.chunk_size == 0

    def test_data_chunk_with_complex_metadata(self):
        """Test DataChunk creation with complex metadata."""
        metadata = ChunkMetadata(
            chunk_id=5,
            chunk_size=100,
            total_chunks=10,
            source_document="doc123",
            section_title="introduction",
        )

        chunk = DataChunk(
            text="Complex chunk with metadata",
            start_idx=500,
            end_idx=600,
            metadata=metadata,
        )

        assert chunk.metadata.chunk_id == 5
        assert chunk.metadata.chunk_size == 100
        assert chunk.metadata.total_chunks == 10
        assert chunk.metadata.source_document == "doc123"
        assert chunk.metadata.section_title == "introduction"


class TestDataChunker:
    """Test DataChunker class."""

    def test_data_chunker_default_initialization(self):
        """Test DataChunker initialization with default parameters."""
        chunker = DataChunker()

        assert chunker.chunk_size == 768
        assert chunker.overlap_size == 100

    def test_data_chunker_custom_initialization(self):
        """Test DataChunker initialization with custom parameters."""
        chunker = DataChunker(chunk_size=512, overlap_size=50)

        assert chunker.chunk_size == 512
        assert chunker.overlap_size == 50

    def test_data_chunker_zero_overlap(self):
        """Test DataChunker initialization with zero overlap."""
        chunker = DataChunker(chunk_size=100, overlap_size=0)

        assert chunker.chunk_size == 100
        assert chunker.overlap_size == 0

    def test_data_chunker_large_overlap(self):
        """Test DataChunker initialization with large overlap."""
        chunker = DataChunker(chunk_size=100, overlap_size=90)

        assert chunker.chunk_size == 100
        assert chunker.overlap_size == 90

    def test_chunk_empty_text(self):
        """Test chunking empty text."""
        chunker = DataChunker()

        result = chunker.chunk("")
        assert result == []

        result = chunker.chunk("   ")
        assert result == []

    def test_chunk_whitespace_only_text(self):
        """Test chunking whitespace-only text."""
        chunker = DataChunker()

        result = chunker.chunk("   \n\t   ")
        assert result == []

    def test_chunk_single_character(self):
        """Test chunking single character text."""
        chunker = DataChunker(chunk_size=10)

        result = chunker.chunk("a")

        assert len(result) == 1
        assert result[0].text == "a"
        assert result[0].start_idx == 0
        assert result[0].end_idx == 1
        assert result[0].metadata.chunk_id == 0
        assert result[0].metadata.chunk_size == 1
        assert result[0].metadata.total_chunks == 1

    def test_chunk_small_text_no_overlap_needed(self):
        """Test chunking small text that fits in one chunk."""
        chunker = DataChunker(chunk_size=100)
        text = "This is a small text that fits in one chunk."

        result = chunker.chunk(text)

        assert len(result) == 1
        assert result[0].text == text
        assert result[0].start_idx == 0
        assert result[0].end_idx == len(text)
        assert result[0].metadata.chunk_id == 0
        assert result[0].metadata.chunk_size == len(text)
        assert result[0].metadata.total_chunks == 1

    def test_chunk_text_exactly_chunk_size(self):
        """Test chunking text that is exactly the chunk size."""
        chunker = DataChunker(chunk_size=10)
        text = "1234567890"  # Exactly 10 characters

        result = chunker.chunk(text)

        assert len(result) == 1
        assert result[0].text == text
        assert result[0].start_idx == 0
        assert result[0].end_idx == 10
        assert result[0].metadata.chunk_size == 10

    def test_chunk_text_requires_multiple_chunks(self):
        """Test chunking text that requires multiple chunks."""
        chunker = DataChunker(chunk_size=5, overlap_size=1)
        text = "1234567890"  # 10 characters, should create 3 chunks

        result = chunker.chunk(text)

        assert len(result) == 3

        # First chunk
        assert result[0].text == "12345"
        assert result[0].start_idx == 0
        assert result[0].end_idx == 5
        assert result[0].metadata.chunk_id == 0
        assert result[0].metadata.total_chunks == 3

        # Second chunk (with overlap)
        assert result[1].text == "56789"
        assert result[1].start_idx == 4  # 5 - 1 overlap
        assert result[1].end_idx == 9
        assert result[1].metadata.chunk_id == 1

        # Third chunk (with overlap)
        assert result[2].text == "90"
        assert result[2].start_idx == 8  # 9 - 1 overlap
        assert result[2].end_idx == 10
        assert result[2].metadata.chunk_id == 2

    def test_chunk_with_zero_overlap(self):
        """Test chunking with zero overlap."""
        chunker = DataChunker(chunk_size=3, overlap_size=0)
        text = "123456789"

        result = chunker.chunk(text)

        assert len(result) == 3

        # First chunk
        assert result[0].text == "123"
        assert result[0].start_idx == 0
        assert result[0].end_idx == 3

        # Second chunk
        assert result[1].text == "456"
        assert result[1].start_idx == 3
        assert result[1].end_idx == 6

        # Third chunk
        assert result[2].text == "789"
        assert result[2].start_idx == 6
        assert result[2].end_idx == 9

    def test_chunk_with_large_overlap(self):
        """Test chunking with large overlap."""
        chunker = DataChunker(chunk_size=5, overlap_size=4)
        text = "1234567890"

        result = chunker.chunk(text)

        assert len(result) == 6  # More chunks due to large overlap

        # Verify overlap behavior
        for i in range(1, len(result)):
            prev_chunk = result[i - 1]
            curr_chunk = result[i]
            # Each chunk should start at least 1 character after the previous
            assert curr_chunk.start_idx >= prev_chunk.start_idx + 1

    def test_chunk_metadata_accuracy(self):
        """Test that chunk metadata is accurate."""
        chunker = DataChunker(chunk_size=4, overlap_size=1)
        text = "1234567890"

        result = chunker.chunk(text)

        # Verify all chunks have correct total_chunks
        for chunk in result:
            assert chunk.metadata.total_chunks == len(result)

        # Verify chunk_id sequence
        for i, chunk in enumerate(result):
            assert chunk.metadata.chunk_id == i

        # Verify chunk_size matches actual text length
        for chunk in result:
            assert chunk.metadata.chunk_size == len(chunk.text)

    def test_chunk_boundary_accuracy(self):
        """Test that chunk boundaries are calculated correctly."""
        chunker = DataChunker(chunk_size=3, overlap_size=1)
        text = "123456789"

        result = chunker.chunk(text)

        # Verify no gaps or overlaps in coverage
        for i, chunk in enumerate(result):
            assert chunk.start_idx >= 0
            assert chunk.end_idx <= len(text)
            assert chunk.start_idx < chunk.end_idx
            assert chunk.text == text[chunk.start_idx : chunk.end_idx]

    def test_chunk_very_long_text(self):
        """Test chunking very long text."""
        chunker = DataChunker(chunk_size=100, overlap_size=10)
        text = "a" * 1000  # 1000 characters

        result = chunker.chunk(text)

        assert len(result) > 1

        # Verify all chunks are properly sized
        for chunk in result:
            assert len(chunk.text) <= chunker.chunk_size
            assert chunk.metadata.chunk_size == len(chunk.text)

        # Verify total coverage
        total_covered = sum(len(chunk.text) for chunk in result)
        # Should cover at least the full text
        assert total_covered >= len(text)

    def test_chunk_single_character_chunk_size(self):
        """Test chunking with chunk size of 1."""
        chunker = DataChunker(chunk_size=1, overlap_size=0)
        text = "abc"

        result = chunker.chunk(text)

        assert len(result) == 3
        assert result[0].text == "a"
        assert result[1].text == "b"
        assert result[2].text == "c"

    def test_chunk_overlap_larger_than_chunk_size(self):
        """Test chunking with overlap larger than chunk size."""
        chunker = DataChunker(chunk_size=3, overlap_size=5)
        text = "123456789"

        result = chunker.chunk(text)

        # Should still work, but with maximum overlap
        assert len(result) >= 1

        # Verify chunks don't exceed chunk size
        for chunk in result:
            assert len(chunk.text) <= chunker.chunk_size

    def test_chunk_unicode_text(self):
        """Test chunking with unicode text."""
        chunker = DataChunker(chunk_size=5, overlap_size=1)
        text = "Hello 世界 🌍"

        result = chunker.chunk(text)

        assert len(result) >= 1

        # Verify all chunks contain valid text
        for chunk in result:
            assert isinstance(chunk.text, str)
            assert len(chunk.text) > 0

    def test_chunk_newlines_and_special_characters(self):
        """Test chunking text with newlines and special characters."""
        chunker = DataChunker(chunk_size=10, overlap_size=2)
        text = "Line 1\nLine 2\tTabbed\r\nWindows line"

        result = chunker.chunk(text)

        assert len(result) >= 1

        # Verify chunks preserve original text structure
        for chunk in result:
            assert chunk.text in text
            assert chunk.start_idx < chunk.end_idx

    def test_chunk_consistency_across_calls(self):
        """Test that chunking the same text produces consistent results."""
        chunker = DataChunker(chunk_size=5, overlap_size=1)
        text = "This is a test text for consistency."

        result1 = chunker.chunk(text)
        result2 = chunker.chunk(text, start_chunk_id=0)

        assert len(result1) == len(result2)

        for chunk1, chunk2 in zip(result1, result2):
            assert chunk1.text == chunk2.text
            assert chunk1.start_idx == chunk2.start_idx
            assert chunk1.end_idx == chunk2.end_idx
            assert chunk1.metadata == chunk2.metadata

    def test_chunk_different_chunker_instances(self):
        """Test that different chunker instances work independently."""
        chunker1 = DataChunker(chunk_size=5, overlap_size=1)
        chunker2 = DataChunker(chunk_size=3, overlap_size=0)
        text = "1234567890"

        result1 = chunker1.chunk(text)
        result2 = chunker2.chunk(text)

        # Results should be different due to different parameters
        assert len(result1) != len(result2)

        # But both should be valid
        for chunk in result1 + result2:
            assert chunk.start_idx >= 0
            assert chunk.end_idx <= len(text)
            assert chunk.text == text[chunk.start_idx : chunk.end_idx]

    def test_chunk_edge_case_minimal_progress(self):
        """Test edge case where overlap might cause minimal progress."""
        chunker = DataChunker(chunk_size=5, overlap_size=4)
        text = "1234567890"

        result = chunker.chunk(text)

        # Should still complete without infinite loop
        assert len(result) > 0

        # Verify we make progress
        for i in range(1, len(result)):
            assert result[i].start_idx > result[i - 1].start_idx

    def test_chunk_parameter_validation(self):
        """Test that chunker handles edge case parameters gracefully."""
        # Test with very small chunk size
        chunker = DataChunker(chunk_size=1, overlap_size=0)
        result = chunker.chunk("abc")
        assert len(result) == 3

        # Test with chunk size larger than text
        chunker = DataChunker(chunk_size=1000, overlap_size=100)
        result = chunker.chunk("short")
        assert len(result) == 1
        assert result[0].text == "short"
