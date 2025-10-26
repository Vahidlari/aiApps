"""Email indexer for the RAG system.

This module handles the indexing of email messages into the RAG system.
It converts email messages into data chunks that can be used for the RAG system.

Key responsibilities:
- Convert email messages into data chunks
- Provide a unified interface for indexing email messages
- Prepare clean text content for the embedding engine
- Maintain email message structure and citation relationships

The indexer returns structured chunks with metadata that can be directly fed to
the embedding engine for vector database storage.
"""

from typing import List

from ragora.core.chunking import ChunkingContextBuilder, DataChunk, DataChunker
from ragora.utils.email_utils.imap_provider import EmailProvider
from ragora.utils.email_utils.models import EmailMessage


class EmailIndexer:
    """Email indexer for the RAG system."""

    def __init__(
        self,
        email_provider: EmailProvider,
        data_chunker: DataChunker,
        email_folders_whitelist: List[str] = None,
        email_folders_blacklist: List[str] = None,
    ):
        self.email_provider = email_provider
        self.data_chunker = data_chunker
        self.email_folders = self.email_provider.get_folders()
        self.email_folders_whitelist = email_folders_whitelist
        self.email_folders_blacklist = email_folders_blacklist

    def chunk_unread_emails(self, start_chunk_id: int = 0) -> List[DataChunk]:
        """
        Chunk unread email messages into data chunks.
        This method is used to fetch unread email messages from the email
        provider and chunk them into data chunks.
        Args:
            start_chunk_id: Starting chunk ID for the unread email messages
        Returns:
            List of data chunks containing the unread email messages
        """
        unread_emails = self.email_provider.fetch_messages(unread_only=True)
        all_chunks = []
        chunk_id_counter = start_chunk_id

        for email in unread_emails:
            chunks = self._email_to_chunks(email, chunk_id_counter)
            all_chunks.extend(chunks)
            chunk_id_counter += len(chunks)

        return all_chunks

    def chunk_all_emails(self, start_chunk_id: int = 0) -> List[DataChunk]:
        """
        Chunk all email messages into data chunks.
        This method is used to fetch all email messages from an email provider and
        chunk them into data chunks.
        Args:
            start_chunk_id: Starting chunk ID for the all email messages
        Returns:
            List of data chunks containing the all email messages
        """
        all_emails = self.email_provider.fetch_messages()
        all_chunks = []
        chunk_id_counter = start_chunk_id

        for email in all_emails:
            chunks = self._email_to_chunks(email, chunk_id_counter)
            all_chunks.extend(chunks)
            chunk_id_counter += len(chunks)

        return all_chunks

    def chunk_email_folder(
        self, folder_name: str, start_chunk_id: int = 0
    ) -> List[DataChunk]:
        """
        Chunk email messages from a specific folder into data chunks.
        This method is used to fetch email messages from a specific folder and
        chunk them into data chunks.
        Args:
            folder_name: Name of the folder to fetch email messages from
            start_chunk_id: Starting chunk ID for the email messages from the folder
        Returns:
            List of data chunks containing the email messages from the folder
        """
        emails = self.email_provider.fetch_messages(folder=folder_name)
        all_chunks = []
        chunk_id_counter = start_chunk_id
        for email in emails:
            chunks = self._email_to_chunks(email, chunk_id_counter)
            all_chunks.extend(chunks)
            chunk_id_counter += len(chunks)
        return all_chunks

    def _email_to_chunks(
        self, email: EmailMessage, start_chunk_id: int
    ) -> List[DataChunk]:
        """
        Convert an EmailMessage to data chunks.

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
                email_date=email.date_sent.isoformat() if email.date_sent else "",
            )
            .with_start_chunk_id(start_chunk_id)
            .build()
        )

        return self.data_chunker.chunk(email_text, context)
