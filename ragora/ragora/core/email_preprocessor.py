"""Email preprocessor for the RAG system.

This module handles the preprocessing of email messages for the RAG system.
It converts email messages into data chunks for the RAG system.

Key responsibilities:
- Convert email messages into data chunks
- Provide a unified interface for preprocessing email messages
- Prepare clean text content for the embedding engine
- Maintain email message structure and metadata
- Clean HTML content and strip quoted replies and signatures

The preprocessor returns structured chunks with metadata that can be directly
fed to the embedding engine for vector database storage.
"""

import re
from typing import List

try:
    import html2text
except ImportError:
    html2text = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    from email_reply_parser import EmailReplyParser
except ImportError:
    EmailReplyParser = None

from ragora.core.chunking import ChunkingContextBuilder, DataChunk, DataChunker
from ragora.utils.email_utils.models import EmailMessage


class EmailPreprocessor:
    """Email preprocessor for the RAG system.

    This class handles the conversion of EmailMessage objects into DataChunks
    suitable for vector storage. It follows the same pattern as
    DocumentPreprocessor for consistency in the codebase.

    Attributes:
        chunker: DataChunker instance for chunking email content
    """

    def __init__(self, chunker: DataChunker = None):
        """Initialize the EmailPreprocessor.

        Args:
            chunker: DataChunker instance (optional)
        """
        if chunker is not None:
            self.chunker = chunker
        else:
            # Create a default chunker
            self.chunker = DataChunker()

    def preprocess_emails(
        self, emails: List[EmailMessage], start_sequence_idx: int = 0
    ) -> List[DataChunk]:
        """Preprocess multiple emails into data chunks.

        This method converts a list of EmailMessage objects into DataChunks
        for storage in the vector database.

        Args:
            emails: List of EmailMessage objects to preprocess
            start_sequence_idx: Starting sequence index for the emails

        Returns:
            List of DataChunks containing the email messages
        """
        all_chunks = []
        chunk_idx_counter = start_sequence_idx

        for email in emails:
            chunks = self._email_to_chunks(email, chunk_idx_counter)
            all_chunks.extend(chunks)
            chunk_idx_counter += len(chunks)

        return all_chunks

    def preprocess_email(
        self, email: EmailMessage, start_sequence_idx: int = 0
    ) -> List[DataChunk]:
        """Preprocess a single email into data chunks.

        This method converts a single EmailMessage object into DataChunks
        for storage in the vector database.

        Args:
            email: EmailMessage object to preprocess
            start_sequence_idx: Starting sequence index for this email

        Returns:
            List of DataChunks containing the email message
        """
        return self._email_to_chunks(email, start_sequence_idx)

    def clean_email_body(self, email: EmailMessage) -> str:
        """Clean email body by converting HTML, stripping replies,
        and removing signatures.

        This method orchestrates all cleaning steps:
        1. Extract body (HTML preferred, fallback to text)
        2. Convert HTML to text (if HTML exists)
        3. Strip quoted replies
        4. Strip signatures
        5. Normalize whitespace

        This method can be used independently to get clean email text
        for processing with LLMs or other text analysis tools without
        chunking the content.

        Args:
            email: EmailMessage object to clean

        Returns:
            Cleaned plain text content. Returns empty string if email
            has no body content.

        Example:
            >>> from ragora import EmailPreprocessor
            >>> from ragora.utils.email_utils.models import EmailMessage
            >>>
            >>> preprocessor = EmailPreprocessor()
            >>> clean_text = preprocessor.clean_email_body(email)
            >>> # Use clean_text with LLM or other processing
        """
        # Step 1: Extract body (HTML preferred, fallback to text)
        body = email.get_body()
        if not body or not body.strip():
            return ""

        # Step 2: Convert HTML to text if it's HTML
        # Check if body is HTML by looking at email.body_html
        # or by checking if body contains HTML tags
        is_html = email.body_html is not None and email.body_html.strip()
        if not is_html:
            # Also check if body_text itself contains HTML tags
            is_html = bool(re.search(r"<[^>]+>", body))

        if is_html:
            text = self._html_to_text(body)
        else:
            text = body

        # Step 3: Strip quoted replies
        text = self._strip_quoted_replies(text)

        # Step 4: Strip signatures
        text = self._strip_signatures(text)

        # Step 5: Normalize whitespace
        text = self._normalize_whitespace(text)

        return text

    def _email_to_chunks(
        self, email: EmailMessage, start_sequence_idx: int
    ) -> List[DataChunk]:
        """Convert an EmailMessage to data chunks.

        Args:
            email: EmailMessage object to convert
            start_sequence_idx: Starting sequence index for this email

        Returns:
            List of DataChunks for this email
        """
        # Clean and extract text content from email
        email_text = self.clean_email_body(email)

        # Create context with email metadata
        context = (
            ChunkingContextBuilder()
            .for_email()
            .with_email_info(
                subject=email.subject or "",
                sender=str(email.sender) if email.sender else "",
                recipient=(
                    ", ".join([str(addr) for addr in email.recipients])
                    if email.recipients
                    else ""
                ),
                email_id=email.message_id or "",
                email_date=(email.date_sent.isoformat() if email.date_sent else ""),
            )
            .with_start_sequence_idx(start_sequence_idx)
            .build()
        )

        return self.chunker.chunk(email_text, context)

    def _html_to_text_html2text(self, html_content: str) -> str:
        """Convert HTML content to plain text using html2text library.

        Args:
            html_content: HTML string to convert

        Returns:
            Plain text representation of the HTML

        Raises:
            ImportError: If html2text library is not available
            Exception: If conversion fails
        """
        if html2text is None:
            raise ImportError("html2text library is not available")

        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_images = True
        h.body_width = 0  # Don't wrap lines
        h.unicode_snob = True  # Use unicode
        text = h.handle(html_content)
        return text.strip()

    def _html_to_text_beautifulsoup(self, html_content: str) -> str:
        """Convert HTML content to plain text using BeautifulSoup4.

        Args:
            html_content: HTML string to convert

        Returns:
            Plain text representation of the HTML

        Raises:
            ImportError: If BeautifulSoup4 library is not available
            Exception: If conversion fails
        """
        if BeautifulSoup is None:
            raise ImportError("BeautifulSoup4 library is not available")

        soup = BeautifulSoup(html_content, "html.parser")
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)
        return text.strip()

    def _html_to_text_regex(self, html_content: str) -> str:
        """Convert HTML content to plain text using basic regex cleanup.

        This is a last-resort fallback method that uses regex to remove
        HTML tags and decode common HTML entities.

        Args:
            html_content: HTML string to convert

        Returns:
            Plain text representation of the HTML
        """
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", html_content)
        # Decode common HTML entities
        text = text.replace("&nbsp;", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        text = text.replace("&#39;", "'")
        return text.strip()

    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML content to plain text.

        Tries multiple approaches in order: html2text, BeautifulSoup4, regex.

        Args:
            html_content: HTML string to convert

        Returns:
            Plain text representation of the HTML
        """
        if not html_content or not html_content.strip():
            return ""

        # Try html2text first (better for email HTML)
        if html2text is not None:
            try:
                return self._html_to_text_html2text(html_content)
            except Exception:
                # Fall through to BeautifulSoup if html2text fails
                pass

        # Fallback to BeautifulSoup4
        if BeautifulSoup is not None:
            try:
                return self._html_to_text_beautifulsoup(html_content)
            except Exception:
                pass

        # Last resort: basic regex cleanup
        return self._html_to_text_regex(html_content)

    def _strip_quoted_replies_library(self, text: str) -> str:
        """Strip quoted reply sections using email_reply_parser library.

        Args:
            text: Email text that may contain quoted replies

        Returns:
            Text with quoted replies removed

        Raises:
            ImportError: If email_reply_parser library is not available
            Exception: If parsing fails
        """
        if EmailReplyParser is None:
            raise ImportError("email_reply_parser library is not available")

        # Parse the email to get the actual reply
        parsed = EmailReplyParser.read(text)
        # Extract only the visible (non-quoted) text
        # Use parsed.reply which contains the reply text without quotes
        reply = parsed.reply
        if reply:
            return reply.strip()
        return ""

    def _strip_quoted_replies_regex(self, text: str) -> str:
        """Strip quoted reply sections using regex-based approach.

        This is a fallback method that uses regex patterns to identify
        and remove common quoted reply formats.

        Args:
            text: Email text that may contain quoted replies

        Returns:
            Text with quoted replies removed
        """
        lines = text.split("\n")
        cleaned_lines = []
        in_quoted_section = False
        in_header_block = False

        # Patterns that indicate start of quoted section
        quote_start_patterns = [
            r"^On .+ wrote:",
            r"^From:",
            r"^-----Original Message-----",
            r"^>+",
            r"^--- .+ ---",
            r"^_{5,}",
            r"^={5,}",
        ]

        # Patterns for email headers (usually follow "From:" in quotes)
        email_header_pattern = r"^[A-Z][a-zA-Z-]+:"

        for line in lines:
            # Check if this line starts a quoted section
            is_quote_start = any(
                re.match(pattern, line, re.IGNORECASE)
                for pattern in quote_start_patterns
            )

            if is_quote_start:
                in_quoted_section = True
                in_header_block = True
                continue

            # If we hit a blank line after being in quoted section,
            # we might be transitioning, but continue checking
            if in_quoted_section:
                # Check if line is an email header (part of quote metadata)
                is_email_header = bool(re.match(email_header_pattern, line))
                if is_email_header:
                    in_header_block = True
                    continue

                # After email headers, if we see a blank line,
                # mark that we're past the header block
                if line.strip() == "":
                    if in_header_block:
                        in_header_block = False
                    continue

                # After headers, everything until we see clear break
                # is quoted content
                if not in_header_block:
                    # This is content after headers - should be quoted
                    continue

                # If we get here, might be actual content again
                # Exit quoted section if we have content before
                if len(cleaned_lines) > 0:
                    in_quoted_section = False
                    in_header_block = False
                    cleaned_lines.append(line)
                else:
                    # No content yet, might still be in quote
                    in_header_block = False
                continue

            in_header_block = False
            cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()

    def _strip_quoted_replies(self, text: str) -> str:
        """Strip quoted reply sections from email text.

        Tries email_reply_parser library first, falls back to regex approach.

        Args:
            text: Email text that may contain quoted replies

        Returns:
            Text with quoted replies removed
        """
        if not text or not text.strip():
            return ""

        if EmailReplyParser is not None:
            try:
                return self._strip_quoted_replies_library(text)
            except Exception:
                # Fall through to regex-based approach if library fails
                pass

        # Fallback regex-based approach for common reply patterns
        return self._strip_quoted_replies_regex(text)

    def _strip_signatures(self, text: str) -> str:
        """Strip email signatures from text.

        Uses regex patterns to identify and remove common signature formats.

        Args:
            text: Email text that may contain signatures

        Returns:
            Text with signatures removed
        """
        if not text or not text.strip():
            return ""

        lines = text.split("\n")
        cleaned_lines = []
        signature_started = False

        # Patterns that indicate signature start
        signature_indicators = [
            r"^--\s*$",  # Two dashes on their own line
            r"^---\s*$",  # Three dashes
            r"^_{3,}$",  # Underscores
            r"^={3,}$",  # Equals signs
            r"^Best regards",
            r"^Regards,",
            r"^Sincerely,",
            r"^Cheers,",
            r"^Thanks,",
            r"^Thank you,",
            r"^Sent from my",
            r"^Get Outlook",
        ]

        for i, line in enumerate(lines):
            # Check if this line starts a signature
            is_signature_start = any(
                re.match(pattern, line, re.IGNORECASE)
                for pattern in signature_indicators
            )

            if is_signature_start:
                signature_started = True
                # Don't include this line
                continue

            if signature_started:
                # Continue skipping lines that look like signature content
                # Stop if we hit a blank line followed by non-signature content
                if line.strip() == "":
                    # Check if next non-blank line is signature content
                    next_non_blank_idx = i + 1
                    while (
                        next_non_blank_idx < len(lines)
                        and lines[next_non_blank_idx].strip() == ""
                    ):
                        next_non_blank_idx += 1

                    if next_non_blank_idx < len(lines):
                        next_line = lines[next_non_blank_idx]
                        # If next line doesn't look like signature,
                        # we're past it
                        if not any(
                            re.match(pattern, next_line, re.IGNORECASE)
                            for pattern in signature_indicators
                        ):
                            # Reset and continue
                            signature_started = False
                            cleaned_lines.append(line)
                    else:
                        # End of text, keep blank lines
                        cleaned_lines.append(line)
                else:
                    # Check if line looks like signature
                    # (contains email, phone, etc.)
                    signature_patterns = [
                        r"@.*\.(com|org|net|edu|gov)",
                        r"\d{3}[-.\s]?\d{3}[-.\s]?\d{4}",  # Phone number
                        r"^www\.",
                        r"^http://",
                        r"^https://",
                    ]
                    if any(
                        re.search(pattern, line, re.IGNORECASE)
                        for pattern in signature_patterns
                    ):
                        continue
                    # After signature delimiter, continue skipping lines
                    # even if they don't match patterns (names, titles, etc.)
                    # Continue skipping all lines after signature start
                    # until we explicitly see content that breaks the pattern
                    # (e.g., a full paragraph of non-signature text)
                    continue
            else:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text.

        Args:
            text: Text to normalize

        Returns:
            Text with normalized whitespace
        """
        if not text:
            return ""

        # Replace multiple spaces with single space
        text = re.sub(r" +", " ", text)
        # Replace multiple newlines with maximum of two
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Remove trailing whitespace from each line
        lines = [line.rstrip() for line in text.split("\n")]
        return "\n".join(lines).strip()
