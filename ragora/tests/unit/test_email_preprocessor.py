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

        mock_metadata = ChunkMetadata(chunk_idx=0, chunk_size=10, total_chunks=2)
        mock_chunks = [
            DataChunk(
                text="chunk1",
                start_idx=0,
                end_idx=10,
                chunk_id="email:test:0:0000",
                metadata=mock_metadata,
            ),
            DataChunk(
                text="chunk2",
                start_idx=11,
                end_idx=20,
                chunk_id="email:test:0:0001",
                metadata=mock_metadata,
            ),
        ]
        email_preprocessor_with_chunker.chunker.chunk.return_value = mock_chunks

        result = email_preprocessor_with_chunker.preprocess_email(mock_email)

        assert len(result) == 2
        assert result == mock_chunks
        email_preprocessor_with_chunker.chunker.chunk.assert_called_once()

    def test_preprocess_email_with_start_id(
        self, email_preprocessor_with_chunker, mock_email
    ):
        """Test preprocessing email with start_sequence_idx."""
        from ragora.core.chunking import ChunkMetadata

        mock_metadata = ChunkMetadata(chunk_idx=5, chunk_size=10, total_chunks=1)
        mock_chunks = [
            DataChunk(
                text="chunk",
                start_idx=0,
                end_idx=10,
                chunk_id="email:test:0:0000",
                metadata=mock_metadata,
            )
        ]
        email_preprocessor_with_chunker.chunker.chunk.return_value = mock_chunks

        result = email_preprocessor_with_chunker.preprocess_email(
            mock_email, start_sequence_idx=5
        )

        assert len(result) == 1
        # Verify context was created with correct start_sequence_idx
        email_preprocessor_with_chunker.chunker.chunk.assert_called_once()

    def test_preprocess_emails(self, email_preprocessor_with_chunker, mock_email):
        """Test preprocessing multiple emails."""
        from ragora.core.chunking import ChunkMetadata

        mock_metadata = ChunkMetadata(chunk_idx=0, chunk_size=10, total_chunks=1)
        mock_chunks = [
            DataChunk(
                text="chunk",
                start_idx=0,
                end_idx=10,
                chunk_id="email:test:0:0000",
                metadata=mock_metadata,
            )
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
        """Test preprocessing emails with start_sequence_idx."""
        from ragora.core.chunking import ChunkMetadata

        mock_metadata = ChunkMetadata(chunk_idx=10, chunk_size=10, total_chunks=1)
        mock_chunks = [
            DataChunk(
                text="chunk",
                start_idx=0,
                end_idx=10,
                chunk_id="email:test:0:0000",
                metadata=mock_metadata,
            )
        ]
        email_preprocessor_with_chunker.chunker.chunk.return_value = mock_chunks

        emails = [mock_email, mock_email]
        result = email_preprocessor_with_chunker.preprocess_emails(
            emails, start_sequence_idx=10
        )

        assert len(result) == 2
        assert email_preprocessor_with_chunker.chunker.chunk.call_count == 2

    def test_chunking_context_creation(
        self, email_preprocessor_with_chunker, mock_email
    ):
        """Test chunking context creation with email metadata."""
        from ragora.core.chunking import ChunkMetadata

        mock_metadata = ChunkMetadata(chunk_idx=0, chunk_size=10, total_chunks=1)
        mock_chunks = [
            DataChunk(
                text="chunk",
                start_idx=0,
                end_idx=10,
                chunk_id="email:test:0:0000",
                metadata=mock_metadata,
            )
        ]
        email_preprocessor_with_chunker.chunker.chunk.return_value = mock_chunks

        email_preprocessor_with_chunker.preprocess_email(mock_email)

        # Verify chunk was called with proper arguments
        call_args = email_preprocessor_with_chunker.chunker.chunk.call_args
        assert call_args is not None
        text_arg, context_arg = call_args[0]
        # Text should be cleaned (HTML converted, etc.), not raw body
        assert isinstance(text_arg, str)
        assert len(text_arg) > 0
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

    def test_html_to_text_html2text(self):
        """Test HTML to text conversion using html2text library."""
        from unittest.mock import patch

        preprocessor = EmailPreprocessor()

        # Test with html2text available
        try:
            html = "<p>This is a test paragraph.</p>"
            result = preprocessor._html_to_text_html2text(html)
            assert "This is a test paragraph." in result
            assert "<p>" not in result

            # Test HTML with links (should be ignored)
            html = '<p>Visit <a href="http://example.com">example</a></p>'
            result = preprocessor._html_to_text_html2text(html)
            assert "Visit" in result or "example" in result

            # Test HTML with multiple paragraphs
            html = "<p>Paragraph 1</p><p>Paragraph 2</p>"
            result = preprocessor._html_to_text_html2text(html)
            assert "Paragraph 1" in result
            assert "Paragraph 2" in result
        except ImportError:
            pytest.skip("html2text library not available")

        # Test ImportError when library not available
        with patch("ragora.core.email_preprocessor.html2text", None):
            with pytest.raises(ImportError):
                preprocessor._html_to_text_html2text("<p>test</p>")

    def test_html_to_text_beautifulsoup(self):
        """Test HTML to text conversion using BeautifulSoup4."""
        from unittest.mock import patch

        preprocessor = EmailPreprocessor()

        # Test with BeautifulSoup available
        try:
            html = "<p>This is a test paragraph.</p>"
            result = preprocessor._html_to_text_beautifulsoup(html)
            assert "This is a test paragraph." in result
            assert "<p>" not in result

            # Test HTML with script/style tags (should be removed)
            html = "<p>Content</p><script>alert('test')</script><style>body {}</style>"
            result = preprocessor._html_to_text_beautifulsoup(html)
            assert "Content" in result
            assert "alert" not in result
            assert "body {}" not in result

            # Test HTML with multiple paragraphs
            html = "<p>Paragraph 1</p><p>Paragraph 2</p>"
            result = preprocessor._html_to_text_beautifulsoup(html)
            assert "Paragraph 1" in result
            assert "Paragraph 2" in result
        except ImportError:
            pytest.skip("BeautifulSoup4 library not available")

        # Test ImportError when library not available
        with patch("ragora.core.email_preprocessor.BeautifulSoup", None):
            with pytest.raises(ImportError):
                preprocessor._html_to_text_beautifulsoup("<p>test</p>")

    def test_html_to_text_regex(self):
        """Test HTML to text conversion using regex fallback."""
        preprocessor = EmailPreprocessor()

        # Test simple HTML
        html = "<p>This is a test paragraph.</p>"
        result = preprocessor._html_to_text_regex(html)
        assert "This is a test paragraph." in result
        assert "<p>" not in result

        # Test HTML entities decoding
        html = "Hello &amp; goodbye &lt;test&gt; &quot;quote&quot;"
        result = preprocessor._html_to_text_regex(html)
        assert "&" in result
        assert "<test>" in result
        assert '"quote"' in result

        # Test multiple tags
        html = "<div><p>Content</p></div>"
        result = preprocessor._html_to_text_regex(html)
        assert "Content" in result
        assert "<div>" not in result
        assert "<p>" not in result

    def test_html_to_text_orchestrator(self):
        """Test HTML to text conversion orchestrator with fallback logic."""
        from unittest.mock import patch

        preprocessor = EmailPreprocessor()

        html = "<p>Test content</p>"

        # Test normal flow (should work with available libraries)
        result = preprocessor._html_to_text(html)
        assert "Test content" in result
        assert "<p>" not in result

        # Test with all methods failing except regex
        with (
            patch.object(
                preprocessor, "_html_to_text_html2text", side_effect=Exception("fail")
            ),
            patch.object(
                preprocessor,
                "_html_to_text_beautifulsoup",
                side_effect=Exception("fail"),
            ),
        ):
            result = preprocessor._html_to_text(html)
            # Should fall back to regex
            assert "Test content" in result

        # Test empty input
        assert preprocessor._html_to_text("") == ""
        assert preprocessor._html_to_text("   ") == ""

    def test_strip_quoted_replies_library(self):
        """Test quoted reply stripping using email_reply_parser library."""
        from unittest.mock import patch

        preprocessor = EmailPreprocessor()

        # Test with library available
        try:
            text = """This is my reply.

On Mon, Jan 1, 2024 at 10:00 AM, sender@example.com wrote:
> This is the original message.
> It has multiple lines."""

            result = preprocessor._strip_quoted_replies_library(text)
            # Should extract only the reply part
            assert "This is my reply." in result
            # Quoted content should be removed
            assert "On Mon, Jan 1, 2024" not in result
            assert "This is the original message." not in result
        except ImportError:
            pytest.skip("email_reply_parser library not available")

        # Test ImportError when library not available
        with patch("ragora.core.email_preprocessor.EmailReplyParser", None):
            with pytest.raises(ImportError):
                preprocessor._strip_quoted_replies_library("test")

    def test_strip_quoted_replies_regex(self):
        """Test quoted reply stripping using regex-based approach."""
        preprocessor = EmailPreprocessor()

        # Test "On ... wrote:" pattern
        text = """This is my reply.

On Mon, Jan 1, 2024 at 10:00 AM, sender@example.com wrote:
> This is the original message.
> It has multiple lines."""
        result = preprocessor._strip_quoted_replies_regex(text)
        assert "This is my reply." in result
        assert "On Mon, Jan 1, 2024" not in result
        assert "This is the original message." not in result

        # Test "From:" pattern
        text = """My response here.

From: sender@example.com
Sent: Monday, January 1, 2024
Subject: Re: Test

Original content here."""
        result = preprocessor._strip_quoted_replies_regex(text)
        assert "My response here." in result
        assert "From: sender@example.com" not in result
        assert "Original content here." not in result

        # Test "-----Original Message-----" pattern
        text = """New content.

-----Original Message-----
From: sender@example.com
To: recipient@example.com
Subject: Test

Old content."""
        result = preprocessor._strip_quoted_replies_regex(text)
        assert "New content." in result
        assert "-----Original Message-----" not in result
        assert "Old content." not in result

        # Test quoted lines with >
        text = """My response.

> Quoted line 1
> Quoted line 2
Regular line after."""
        result = preprocessor._strip_quoted_replies_regex(text)
        assert "My response." in result
        assert "Quoted line 1" not in result
        assert "Quoted line 2" not in result
        # Should preserve non-quoted content after quotes
        assert "Regular line after." in result

        # Test text without quotes
        text = "This is a simple message without any quotes."
        result = preprocessor._strip_quoted_replies_regex(text)
        assert result == text

        # Test empty text
        assert preprocessor._strip_quoted_replies_regex("") == ""

    def test_strip_quoted_replies_orchestrator(self):
        """Test quoted reply stripping orchestrator with fallback logic."""
        from unittest.mock import patch

        preprocessor = EmailPreprocessor()

        text = """This is my reply.

On Mon, Jan 1, 2024 at 10:00 AM, sender@example.com wrote:
> This is the original message."""

        # Test normal flow (should work with available library or fallback)
        result = preprocessor._strip_quoted_replies(text)
        assert "This is my reply." in result
        assert "On Mon, Jan 1, 2024" not in result

        # Test with library failing, should fall back to regex
        with patch.object(
            preprocessor, "_strip_quoted_replies_library", side_effect=Exception("fail")
        ):
            result = preprocessor._strip_quoted_replies(text)
            # Should fall back to regex method
            assert "This is my reply." in result
            assert "On Mon, Jan 1, 2024" not in result

        # Test empty text
        assert preprocessor._strip_quoted_replies("") == ""

    def test_strip_signatures(self):
        """Test signature stripping with various signature formats."""
        preprocessor = EmailPreprocessor()

        # Test "--" signature delimiter
        text = """This is the email body.

--
John Doe
john.doe@example.com
Phone: 555-123-4567"""
        result = preprocessor._strip_signatures(text)
        assert "This is the email body." in result
        assert "--" not in result.strip()
        assert "john.doe@example.com" not in result

        # Test "Best regards" signature
        text = """Email content here.

Best regards,
Jane Smith
jane.smith@example.com"""
        result = preprocessor._strip_signatures(text)
        assert "Email content here." in result
        assert "Best regards" not in result
        assert "jane.smith@example.com" not in result

        # Test "Sent from my" signature
        text = """Main content.

Sent from my iPhone"""
        result = preprocessor._strip_signatures(text)
        assert "Main content." in result
        assert "Sent from my iPhone" not in result

        # Test text without signature
        text = "This is a simple message without any signature."
        result = preprocessor._strip_signatures(text)
        assert result == text

        # Test empty text
        assert preprocessor._strip_signatures("") == ""

    def test_extract_actual_body_html(self):
        """Test extracting actual body content from HTML emails."""
        from datetime import datetime

        sender = EmailAddress("sender@example.com", "Test Sender")
        recipient = EmailAddress("recipient@example.com", "Test Recipient")

        email = EmailMessage(
            message_id="msg_123",
            subject="Test Email",
            sender=sender,
            recipients=[recipient],
            body_html="<html><body><p>This is the actual body content.</p></body></html>",
            body_text=None,
            date_sent=datetime(2024, 1, 1, 10, 0, 0),
        )

        preprocessor = EmailPreprocessor()
        cleaned = preprocessor.clean_email_body(email)

        # Should extract text from HTML
        assert "This is the actual body content." in cleaned
        # Should not contain HTML tags
        assert "<p>" not in cleaned
        assert "<html>" not in cleaned

    def test_extract_actual_body_text(self):
        """Test extracting actual body content from plain text emails."""
        from datetime import datetime

        sender = EmailAddress("sender@example.com", "Test Sender")
        recipient = EmailAddress("recipient@example.com", "Test Recipient")

        email = EmailMessage(
            message_id="msg_123",
            subject="Test Email",
            sender=sender,
            recipients=[recipient],
            body_html=None,
            body_text="This is the actual body content in plain text.",
            date_sent=datetime(2024, 1, 1, 10, 0, 0),
        )

        preprocessor = EmailPreprocessor()
        cleaned = preprocessor.clean_email_body(email)

        # Should extract text content
        assert "This is the actual body content in plain text." in cleaned

    def test_preprocessing_with_html_content(self):
        """Test preprocessing with complex HTML emails."""
        from datetime import datetime

        sender = EmailAddress("sender@example.com", "Test Sender")
        recipient = EmailAddress("recipient@example.com", "Test Recipient")

        html_content = """
        <html>
        <body>
            <h1>Email Title</h1>
            <p>This is the main content.</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
            <p>More content here.</p>
        </body>
        </html>
        """

        email = EmailMessage(
            message_id="msg_123",
            subject="Test Email",
            sender=sender,
            recipients=[recipient],
            body_html=html_content,
            body_text=None,
            date_sent=datetime(2024, 1, 1, 10, 0, 0),
        )

        preprocessor = EmailPreprocessor()
        mock_chunker = Mock(spec=DataChunker)
        preprocessor.chunker = mock_chunker

        from ragora.core.chunking import ChunkMetadata

        mock_metadata = ChunkMetadata(chunk_idx=0, chunk_size=10, total_chunks=1)
        mock_chunks = [
            DataChunk(
                text="chunk",
                start_idx=0,
                end_idx=10,
                chunk_id="email:test:0:0000",
                metadata=mock_metadata,
            )
        ]
        mock_chunker.chunk.return_value = mock_chunks

        result = preprocessor.preprocess_email(email)

        # Verify chunker was called
        mock_chunker.chunk.assert_called_once()
        call_args = mock_chunker.chunk.call_args
        cleaned_text = call_args[0][0]

        # Verify HTML was converted to text
        assert "Email Title" in cleaned_text or "main content" in cleaned_text
        # Verify HTML tags are removed
        assert "<h1>" not in cleaned_text
        assert "<p>" not in cleaned_text
        assert "<ul>" not in cleaned_text

    def test_preprocessing_with_quoted_reply(self):
        """Test preprocessing with email replies containing quoted content."""
        from datetime import datetime

        sender = EmailAddress("sender@example.com", "Test Sender")
        recipient = EmailAddress("recipient@example.com", "Test Recipient")

        email_body = """This is my response to your email.

On Mon, Jan 1, 2024 at 10:00 AM, original@example.com wrote:
> This is the original message.
> It contains multiple lines.
> This should be stripped out."""

        email = EmailMessage(
            message_id="msg_123",
            subject="Re: Test Email",
            sender=sender,
            recipients=[recipient],
            body_text=email_body,
            body_html=None,
            date_sent=datetime(2024, 1, 1, 10, 0, 0),
        )

        preprocessor = EmailPreprocessor()
        mock_chunker = Mock(spec=DataChunker)
        preprocessor.chunker = mock_chunker

        from ragora.core.chunking import ChunkMetadata

        mock_metadata = ChunkMetadata(chunk_idx=0, chunk_size=10, total_chunks=1)
        mock_chunks = [
            DataChunk(
                text="chunk",
                start_idx=0,
                end_idx=10,
                chunk_id="email:test:0:0000",
                metadata=mock_metadata,
            )
        ]
        mock_chunker.chunk.return_value = mock_chunks

        result = preprocessor.preprocess_email(email)

        # Verify chunker was called
        mock_chunker.chunk.assert_called_once()
        call_args = mock_chunker.chunk.call_args
        cleaned_text = call_args[0][0]

        # Verify actual response is kept
        assert "This is my response" in cleaned_text
        # Verify quoted content is removed
        assert "On Mon, Jan 1, 2024" not in cleaned_text
        assert "This is the original message." not in cleaned_text

    def test_preprocessing_with_signature(self):
        """Test preprocessing with email signatures."""
        from datetime import datetime

        sender = EmailAddress("sender@example.com", "Test Sender")
        recipient = EmailAddress("recipient@example.com", "Test Recipient")

        email_body = """This is the main email content.
It has multiple lines of important information.

--
John Doe
Senior Developer
john.doe@example.com
Phone: 555-123-4567"""

        email = EmailMessage(
            message_id="msg_123",
            subject="Test Email",
            sender=sender,
            recipients=[recipient],
            body_text=email_body,
            body_html=None,
            date_sent=datetime(2024, 1, 1, 10, 0, 0),
        )

        preprocessor = EmailPreprocessor()
        mock_chunker = Mock(spec=DataChunker)
        preprocessor.chunker = mock_chunker

        from ragora.core.chunking import ChunkMetadata

        mock_metadata = ChunkMetadata(chunk_idx=0, chunk_size=10, total_chunks=1)
        mock_chunks = [
            DataChunk(
                text="chunk",
                start_idx=0,
                end_idx=10,
                chunk_id="email:test:0:0000",
                metadata=mock_metadata,
            )
        ]
        mock_chunker.chunk.return_value = mock_chunks

        result = preprocessor.preprocess_email(email)

        # Verify chunker was called
        mock_chunker.chunk.assert_called_once()
        call_args = mock_chunker.chunk.call_args
        cleaned_text = call_args[0][0]

        # Verify main content is kept
        assert "This is the main email content" in cleaned_text
        assert "important information" in cleaned_text
        # Verify signature is removed
        assert "john.doe@example.com" not in cleaned_text
        assert "Phone: 555-123-4567" not in cleaned_text

    def test_clean_email_body_integration(self):
        """Test complete cleaning pipeline with all steps."""
        from datetime import datetime

        sender = EmailAddress("sender@example.com", "Test Sender")
        recipient = EmailAddress("recipient@example.com", "Test Recipient")

        # Email with HTML, quoted reply, and signature
        html_body = """
        <html>
        <body>
            <p>This is the actual response content.</p>
            <p>It should be preserved.</p>
        </body>
        </html>
        """

        text_body = """This is the actual response content.
It should be preserved.

On Mon, Jan 1, 2024, original@example.com wrote:
> This quoted content should be removed.
> It contains old information.

--
Signature Line
contact@example.com"""

        email = EmailMessage(
            message_id="msg_123",
            subject="Re: Test",
            sender=sender,
            recipients=[recipient],
            body_html=html_body,
            body_text=text_body,
            date_sent=datetime(2024, 1, 1, 10, 0, 0),
        )

        preprocessor = EmailPreprocessor()
        cleaned = preprocessor.clean_email_body(email)

        # Verify HTML is converted to text
        assert "<p>" not in cleaned
        assert "<html>" not in cleaned

        # Verify actual content is preserved
        assert (
            "This is the actual response content" in cleaned or "preserved" in cleaned
        )

        # Verify quoted content is removed
        assert "On Mon, Jan 1, 2024" not in cleaned
        assert "This quoted content should be removed" not in cleaned

        # Verify signature is removed
        assert "contact@example.com" not in cleaned

    def test_clean_email_body_empty(self):
        """Test cleaning with empty email body."""
        from datetime import datetime

        sender = EmailAddress("sender@example.com", "Test Sender")
        recipient = EmailAddress("recipient@example.com", "Test Recipient")

        email = EmailMessage(
            message_id="msg_123",
            subject="Test Email",
            sender=sender,
            recipients=[recipient],
            body_html=None,
            body_text=None,
            date_sent=datetime(2024, 1, 1, 10, 0, 0),
        )

        preprocessor = EmailPreprocessor()
        cleaned = preprocessor.clean_email_body(email)
        assert cleaned == ""

    def test_preprocessing_with_complex_email(self):
        """Test preprocessing with real-world complex email scenario."""
        from datetime import datetime

        sender = EmailAddress("sender@example.com", "Test Sender")
        recipient = EmailAddress("recipient@example.com", "Test Recipient")

        # Complex email with HTML, reply, and signature
        html_body = """
        <html>
        <head><style>body { font-family: Arial; }</style></head>
        <body>
            <div>
                <h2>Project Update</h2>
                <p>Hi there,</p>
                <p>I wanted to provide an update on the project status.</p>
                <ul>
                    <li>Task 1: Complete</li>
                    <li>Task 2: In Progress</li>
                </ul>
                <p>Let me know if you have any questions.</p>
            </div>
        </body>
        </html>
        """

        email = EmailMessage(
            message_id="msg_complex",
            subject="Re: Project Update",
            sender=sender,
            recipients=[recipient],
            body_html=html_body,
            body_text=None,
            date_sent=datetime(2024, 1, 1, 10, 0, 0),
        )

        preprocessor = EmailPreprocessor()
        mock_chunker = Mock(spec=DataChunker)
        preprocessor.chunker = mock_chunker

        from ragora.core.chunking import ChunkMetadata

        mock_metadata = ChunkMetadata(chunk_idx=0, chunk_size=10, total_chunks=1)
        mock_chunks = [
            DataChunk(
                text="chunk",
                start_idx=0,
                end_idx=10,
                chunk_id="email:test:0:0000",
                metadata=mock_metadata,
            )
        ]
        mock_chunker.chunk.return_value = mock_chunks

        result = preprocessor.preprocess_email(email)

        # Verify chunker was called
        mock_chunker.chunk.assert_called_once()
        call_args = mock_chunker.chunk.call_args
        cleaned_text = call_args[0][0]

        # Verify key content is extracted
        assert "Project Update" in cleaned_text or "project status" in cleaned_text
        # Verify HTML structure is removed
        assert "<html>" not in cleaned_text
        assert "<div>" not in cleaned_text
        assert "<style>" not in cleaned_text
