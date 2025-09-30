"""Data models for email functionality."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MessageStatus(Enum):
    """Status of an email message."""

    UNREAD = "unread"
    READ = "read"
    DRAFT = "draft"
    SENT = "sent"
    TRASH = "trash"


@dataclass
class EmailAddress:
    """Represents an email address with optional display name."""

    email: str
    name: Optional[str] = None

    def __str__(self) -> str:
        if self.name:
            return f"{self.name} <{self.email}>"
        return self.email


@dataclass
class EmailAttachment:
    """Represents an email attachment."""

    filename: str
    content_type: str
    size: int
    content: Optional[bytes] = None
    content_id: Optional[str] = None  # For inline attachments

    def __post_init__(self):
        if self.content and len(self.content) != self.size:
            self.size = len(self.content)


@dataclass
class EmailMessage:
    """Represents an email message."""

    message_id: str
    subject: str
    sender: EmailAddress
    recipients: List[EmailAddress]
    cc_recipients: List[EmailAddress] = field(default_factory=list)
    bcc_recipients: List[EmailAddress] = field(default_factory=list)
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    date_sent: Optional[datetime] = None
    date_received: Optional[datetime] = None
    status: MessageStatus = MessageStatus.UNREAD
    attachments: List[EmailAttachment] = field(default_factory=list)
    thread_id: Optional[str] = None
    conversation_id: Optional[str] = None
    folder: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_body(self) -> str:
        """Get the best available body content (HTML preferred, fallback to text)."""
        return self.body_html if self.body_html else (self.body_text or "")

    def get_all_recipients(self) -> List[EmailAddress]:
        """Get all recipients including CC and BCC."""
        return self.recipients + self.cc_recipients + self.bcc_recipients


@dataclass
class EmailDraft:
    """Represents a draft email message."""

    draft_id: str
    subject: str
    recipients: List[EmailAddress]
    cc_recipients: List[EmailAddress] = field(default_factory=list)
    bcc_recipients: List[EmailAddress] = field(default_factory=list)
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    attachments: List[EmailAttachment] = field(default_factory=list)
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_body(self) -> str:
        """Get the best available body content (HTML preferred, fallback to text)."""
        return self.body_html if self.body_html else (self.body_text or "")

    def get_all_recipients(self) -> List[EmailAddress]:
        """Get all recipients including CC and BCC."""
        return self.recipients + self.cc_recipients + self.bcc_recipients


@dataclass
class EmailCredentials:
    """Base class for email credentials."""

    pass


@dataclass
class IMAPCredentials(EmailCredentials):
    """Credentials for IMAP/SMTP servers."""

    imap_server: str
    imap_port: int
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    use_ssl: bool = True
    use_tls: bool = False


@dataclass
class GraphCredentials(EmailCredentials):
    """Credentials for Microsoft Graph API."""

    client_id: str
    client_secret: str
    tenant_id: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
