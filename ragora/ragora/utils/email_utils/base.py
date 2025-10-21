"""Base email provider interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from .models import EmailCredentials, EmailDraft, EmailMessage


class EmailProvider(ABC):
    """Abstract base class for email providers.

    This interface defines the contract that all email providers must implement,
    allowing the RAG system to work with different email backends seamlessly.
    """

    def __init__(self, credentials: EmailCredentials):
        """Initialize the email provider with credentials.

        Args:
            credentials: Provider-specific credentials for authentication
        """
        self.credentials = credentials

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the email service.

        Raises:
            ConnectionError: If connection fails
            AuthenticationError: If authentication fails
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to the email service."""
        pass

    @abstractmethod
    def fetch_messages(
        self, limit: int = 50, folder: Optional[str] = None, unread_only: bool = False
    ) -> List[EmailMessage]:
        """Fetch messages from the email service.

        Args:
            limit: Maximum number of messages to fetch
            folder: Specific folder to fetch from (None for inbox)
            unread_only: If True, only fetch unread messages

        Returns:
            List of EmailMessage objects

        Raises:
            ConnectionError: If not connected
            FetchError: If message fetching fails
        """
        pass

    @abstractmethod
    def fetch_message_by_id(self, message_id: str) -> Optional[EmailMessage]:
        """Fetch a specific message by its ID.

        Args:
            message_id: Unique identifier for the message

        Returns:
            EmailMessage object or None if not found

        Raises:
            ConnectionError: If not connected
            FetchError: If message fetching fails
        """
        pass

    @abstractmethod
    def create_draft(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        folder: str = "Drafts",
    ) -> EmailDraft:
        """Create a draft message.

        Args:
            to: List of recipient email addresses
            subject: Email subject line
            body: Email body content (HTML or plain text)
            cc: Optional list of CC recipient email addresses
            bcc: Optional list of BCC recipient email addresses
            attachments: Optional list of file paths to attach
            folder: Folder to store the draft in (default: "Drafts")

        Returns:
            EmailDraft object with the created draft

        Raises:
            ConnectionError: If not connected
            DraftError: If draft creation fails
        """
        pass

    @abstractmethod
    def send_message(self, draft_id: str, folder: str = "Drafts") -> bool:
        """Send a draft message.

        Args:
            draft_id: ID of the draft to send
            folder: Folder where the draft is stored (default: "Drafts")

        Returns:
            True if message was sent successfully

        Raises:
            ConnectionError: If not connected
            SendError: If message sending fails
        """
        pass

    @abstractmethod
    def send_message_direct(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
    ) -> bool:
        """Send a message directly without creating a draft.

        Args:
            to: List of recipient email addresses
            subject: Email subject line
            body: Email body content (HTML or plain text)
            cc: Optional list of CC recipient email addresses
            bcc: Optional list of BCC recipient email addresses
            attachments: Optional list of file paths to attach

        Returns:
            True if message was sent successfully

        Raises:
            ConnectionError: If not connected
            SendError: If message sending fails
        """
        pass

    @abstractmethod
    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read.

        Args:
            message_id: ID of the message to mark as read

        Returns:
            True if message was marked as read successfully

        Raises:
            ConnectionError: If not connected
            UpdateError: If marking fails
        """
        pass

    @abstractmethod
    def get_folders(self) -> List[str]:
        """Get list of available folders.

        Returns:
            List of folder names

        Raises:
            ConnectionError: If not connected
            FetchError: If folder fetching fails
        """
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the provider is connected to the email service.

        Returns:
            True if connected, False otherwise
        """
        pass
