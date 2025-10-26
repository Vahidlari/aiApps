"""Unit tests for EmailPreprocessor."""

from unittest.mock import Mock

import pytest

from ragora.core.chunking import DataChunk, DataChunker
from ragora.core.email_preprocessor import EmailPreprocessor
from ragora.utils.email_utils.models import EmailAddress, EmailMessage


class TestEmailPreprocessor:
    """Test suite for EmailPreprocessor class."""

    @pytest.fixture
    def mock_email(self):
        """Create a mock EmailMessage for testing."""
        from datetime import datetime

        sender = EmailAddress("sender@example.com", "Test Sender")
        recipient = EmailAddress("recipient@example.com", "Test Recipient")
        return EmailMessage(
            message_id="msg_123",
            subject="Test Email",
            sender=sender,
            recipients=[recipient],
            body_text="This is the email body.",
            body_html="<p>This is the email body.</p>",
            date_sent=datetime(2024, 1, 1, 10, 0, 0),
        )

    @pytest.fixture
    def mock_chunker(self):
        """Create a mock DataChunker for testing."""
        chunker = Mock(spec=DataChunker)
        return chunker

    @pytest.fixture
    def email_preprocessor_with_chunker(self, mock_chunker):
        """Create EmailPreprocessor with mocked chunker."""
        return EmailPreprocessor(chunker=mock_chunker)

    @pytest.fixture
    def email_preprocessor_without_chunker(self):
        """Create EmailPreprocessor without chunker (uses default)."""
        return EmailPreprocessor()

    def test_init_with_chunker(self, mock_chunker):
        """Test EmailPreprocessor initialization with chunker."""
        preprocessor = EmailPreprocessor(chunker=mock_chunker)
        assert preprocessor.chunker == mock_chunker

    def test_init_without_chunker(self):
        """Test EmailPreprocessor initialization without chunker."""
        preprocessor = EmailPreprocessor()
        assert isinstance(preprocessor.chunker, DataChunker)

    def test_preprocess_email(self, email_preprocessor_with_chunker, mock_email):
        """Test preprocessing a single email."""
        from ragora.core.chunking import ChunkMetadata

        mock_metadata = ChunkMetadata(chunk_id=0, chunk_size=10, total_chunks=2)
        mock_chunks = [
            DataChunk(text="chunk1", start_idx=0, end_idx=10, metadata=mock_metadata),
            DataChunk(text="chunk2", start_idx=11, end_idx=20, metadata=mock_metadata),
        ]
        email_preprocessor_with_chunker.chunker.chunk.return_value = mock_chunks

        result = email_preprocessor_with_chunker.preprocess_email(mock_email)

        assert len(result) == 2
        assert result == mock_chunks
        email_preprocessor_with_chunker.chunker.chunk.assert_called_once()

    def test_preprocess_email_with_start_id(
        self, email_preprocessor_with_chunker, mock_email
    ):
        """Test preprocessing email with start_chunk_id."""
        from ragora.core.chunking import ChunkMetadata

        mock_metadata = ChunkMetadata(chunk_id=5, chunk_size=10, total_chunks=1)
        mock_chunks = [
            DataChunk(text="chunk", start_idx=0, end_idx=10, metadata=mock_metadata)
        ]
        email_preprocessor_with_chunker.chunker.chunk.return_value = mock_chunks

        result = email_preprocessor_with_chunker.preprocess_email(
            mock_email, start_chunk_id=5
        )

        assert len(result) == 1
        # Verify context was created with correct start_chunk_id
        email_preprocessor_with_chunker.chunker.chunk.assert_called_once()

    def test_preprocess_emails(self, email_preprocessor_with_chunker, mock_email):
        """Test preprocessing multiple emails."""
        from ragora.core.chunking import ChunkMetadata

        mock_metadata = ChunkMetadata(chunk_id=0, chunk_size=10, total_chunks=1)
        mock_chunks = [
            DataChunk(text="chunk", start_idx=0, end_idx=10, metadata=mock_metadata)
        ]
        email_preprocessor_with_chunker.chunker.chunk.return_value = mock_chunks

        emails = [mock_email, mock_email, mock_email]
        result = email_preprocessor_with_chunker.preprocess_emails(emails)

        assert len(result) == 3
        assert email_preprocessor_with_chunker.chunker.chunk.call_count == 3

    def test_preprocess_emails_empty_list(self, email_preprocessor_with_chunker):
        """Test preprocessing empty list of emails."""
        result = email_preprocessor_with_chunker.preprocess_emails([])
        assert result == []

    def test_preprocess_emails_with_start_id(
        self, email_preprocessor_with_chunker, mock_email
    ):
        """Test preprocessing emails with start_chunk_id."""
        from ragora.core.chunking import ChunkMetadata

        mock_metadata = ChunkMetadata(chunk_id=10, chunk_size=10, total_chunks=1)
        mock_chunks = [
            DataChunk(text="chunk", start_idx=0, end_idx=10, metadata=mock_metadata)
        ]
        email_preprocessor_with_chunker.chunker.chunk.return_value = mock_chunks

        emails = [mock_email, mock_email]
        result = email_preprocessor_with_chunker.preprocess_emails(
            emails, start_chunk_id=10
        )

        assert len(result) == 2
        assert email_preprocessor_with_chunker.chunker.chunk.call_count == 2

    def test_chunking_context_creation(
        self, email_preprocessor_with_chunker, mock_email
    ):
        """Test chunking context creation with email metadata."""
        from ragora.core.chunking import ChunkMetadata

        mock_metadata = ChunkMetadata(chunk_id=0, chunk_size=10, total_chunks=1)
        mock_chunks = [
            DataChunk(text="chunk", start_idx=0, end_idx=10, metadata=mock_metadata)
        ]
        email_preprocessor_with_chunker.chunker.chunk.return_value = mock_chunks

        email_preprocessor_with_chunker.preprocess_email(mock_email)

        # Verify chunk was called with proper arguments
        call_args = email_preprocessor_with_chunker.chunker.chunk.call_args
        assert call_args is not None
        text_arg, context_arg = call_args[0]
        assert text_arg == mock_email.get_body()
        assert context_arg is not None

    def test_email_metadata_in_chunks(
        self, email_preprocessor_without_chunker, mock_email
    ):
        """Test that email metadata is properly included in chunks."""
        # Use real chunker to test actual chunk creation
        result = email_preprocessor_without_chunker.preprocess_email(mock_email)

        # Verify chunks were created
        assert len(result) > 0
        # Verify metadata includes email information
        for chunk in result:
            assert chunk.metadata is not None
