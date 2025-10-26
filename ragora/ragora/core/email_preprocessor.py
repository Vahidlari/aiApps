"""Email preprocessor for the RAG system.

This module handles the preprocessing of email messages for the RAG system.
It converts email messages into data chunks for the RAG system.

Key responsibilities:
- Convert email messages into data chunks
- Provide a unified interface for preprocessing email messages
- Prepare clean text content for the embedding engine
- Maintain email message structure and metadata

The preprocessor returns structured chunks with metadata that can be directly
fed to the embedding engine for vector database storage.
"""

from typing import List

from ragora.core.chunking import ChunkingContextBuilder, DataChunk, DataChunker
from ragora.utils.email_utils.models import EmailMessage


class EmailPreprocessor:
    """Email preprocessor for the RAG system.

    This class handles the conversion of EmailMessage objects into DataChunks
    suitable for vector storage. It follows the same pattern as
    DocumentPreprocessor for consistency in the codebase.

    Attributes:
        data_chunker: DataChunker instance for chunking email content
    """

    def __init__(self, data_chunker: DataChunker = None):
        """Initialize the EmailPreprocessor.

        Args:
            data_chunker: DataChunker instance (optional)
        """
        if data_chunker is not None:
            self.data_chunker = data_chunker
        else:
            # Create a default chunker
            self.data_chunker = DataChunker()

    def preprocess_emails(
        self, emails: List[EmailMessage], start_chunk_id: int = 0
    ) -> List[DataChunk]:
        """Preprocess multiple emails into data chunks.

        This method converts a list of EmailMessage objects into DataChunks
        for storage in the vector database.

        Args:
            emails: List of EmailMessage objects to preprocess
            start_chunk_id: Starting chunk ID for the emails

        Returns:
            List of DataChunks containing the email messages
        """
        all_chunks = []
        chunk_id_counter = start_chunk_id

        for email in emails:
            chunks = self._email_to_chunks(email, chunk_id_counter)
            all_chunks.extend(chunks)
            chunk_id_counter += len(chunks)

        return all_chunks

    def preprocess_email(
        self, email: EmailMessage, start_chunk_id: int = 0
    ) -> List[DataChunk]:
        """Preprocess a single email into data chunks.

        This method converts a single EmailMessage object into DataChunks
        for storage in the vector database.

        Args:
            email: EmailMessage object to preprocess
            start_chunk_id: Starting chunk ID for this email

        Returns:
            List of DataChunks containing the email message
        """
        return self._email_to_chunks(email, start_chunk_id)

    def _email_to_chunks(
        self, email: EmailMessage, start_chunk_id: int
    ) -> List[DataChunk]:
        """Convert an EmailMessage to data chunks.

        Args:
            email: EmailMessage object to convert
            start_chunk_id: Starting chunk ID for this email

        Returns:
            List of DataChunks for this email
        """
        # Extract text content from email
        email_text = email.get_body()

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
            .with_start_chunk_id(start_chunk_id)
            .build()
        )

        return self.data_chunker.chunk(email_text, context)
