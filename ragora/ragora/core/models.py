"""Domain models for retrieval results.

This module contains the core data models used for retrieval operations in the
RAG system. These models represent the structured data returned from search
and retrieval operations, providing type-safe access to chunk content,
metadata, and search scores.

Key Models:
- RetrievalMetadata: Structured metadata extracted from stored properties
- RetrievalResultItem: Base class for all chunk retrieval results
- SearchResultItem: Search results with scores (extends RetrievalResultItem)
- EmailMessageModel: Pydantic model for email messages (compatible with EmailMessage)
- EmailListResult: Container for email list results with metadata
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, TypedDict, Union

from pydantic import BaseModel, Field, field_validator, model_validator

from ragora.utils.email_utils.models import (
    EmailAddress,
    EmailAttachment,
    EmailMessage,
    MessageStatus,
)


class EmailAddressDict(TypedDict):
    """TypedDict for email address representation.

    This ensures 'email' is always required and non-null,
    while 'name' remains optional.
    """

    email: str  # Required, non-null email address
    name: Optional[str]  # Optional display name


class RetrievalMetadata(BaseModel):
    """Structured metadata for search results.

    Extracts and organizes metadata fields from stored properties,
    providing type-safe access to chunk, document, and email metadata.
    """

    # Chunk metadata
    chunk_idx: Optional[int] = Field(default=None, description="Chunk index")
    chunk_size: Optional[int] = Field(default=None, description="Chunk size")
    total_chunks: Optional[int] = Field(
        default=None, description="Total chunks in document"
    )
    created_at: Optional[str] = Field(default=None, description="Creation timestamp")

    # Document metadata
    source_document: Optional[str] = Field(
        default=None, description="Source document filename"
    )
    page_number: Optional[int] = Field(default=None, description="Page number")
    section_title: Optional[str] = Field(
        default=None, description="Section or chapter title"
    )
    chunk_type: Optional[str] = Field(
        default=None,
        description="Type of chunk (text, citation, equation, etc.)",
    )

    # Email metadata
    email_subject: Optional[str] = Field(default=None, description="Email subject line")
    email_sender: Optional[str] = Field(
        default=None, description="Email sender address"
    )
    email_recipient: Optional[str] = Field(
        default=None, description="Email recipient address"
    )
    email_date: Optional[str] = Field(default=None, description="Email timestamp")
    email_id: Optional[str] = Field(default=None, description="Unique email identifier")
    email_folder: Optional[str] = Field(default=None, description="Email folder/path")

    # Custom metadata
    custom_metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Custom metadata dictionary"
    )
    language: Optional[str] = Field(
        default=None, description="Content language (e.g., en, es, fr)"
    )
    domain: Optional[str] = Field(
        default=None,
        description="Content domain (e.g., scientific, legal, medical)",
    )
    confidence: Optional[float] = Field(
        default=None, description="Processing confidence score (0.0-1.0)"
    )
    tags: Optional[str] = Field(
        default=None, description="Comma-separated tags/categories"
    )
    priority: Optional[int] = Field(
        default=None, description="Content priority/importance level"
    )
    content_category: Optional[str] = Field(
        default=None, description="Fine-grained content categorization"
    )

    @classmethod
    def from_properties(cls, properties: Dict[str, Any]) -> "RetrievalMetadata":
        """Create RetrievalMetadata from properties dictionary.

        Args:
            properties: Dictionary containing stored properties

        Returns:
            RetrievalMetadata instance
        """
        # Parse custom_metadata JSON string if present
        custom_meta = properties.get("custom_metadata")
        if custom_meta:
            if isinstance(custom_meta, str):
                try:
                    custom_meta = json.loads(custom_meta) if custom_meta else None
                except (json.JSONDecodeError, TypeError):
                    custom_meta = None
            elif not isinstance(custom_meta, dict):
                custom_meta = None
        else:
            custom_meta = None

        return cls(
            chunk_idx=properties.get("metadata_chunk_idx"),
            chunk_size=properties.get("metadata_chunk_size"),
            total_chunks=properties.get("metadata_total_chunks"),
            created_at=properties.get("metadata_created_at")
            or properties.get("created_at"),
            source_document=properties.get("source_document"),
            page_number=properties.get("page_number"),
            section_title=properties.get("section_title"),
            chunk_type=properties.get("chunk_type"),
            email_subject=properties.get("email_subject"),
            email_sender=properties.get("email_sender"),
            email_recipient=properties.get("email_recipient"),
            email_date=properties.get("email_date"),
            email_id=properties.get("email_id"),
            email_folder=properties.get("email_folder"),
            custom_metadata=custom_meta,
            language=properties.get("language"),
            domain=properties.get("domain"),
            confidence=properties.get("confidence"),
            tags=properties.get("tags"),
            priority=properties.get("priority"),
            content_category=properties.get("content_category"),
        )


class RetrievalResultItem(BaseModel):
    """Base class for all chunk retrieval results.

    Contains common fields shared by both direct retrieval and search
    results. This base class provides the core chunk data without
    retrieval-specific context.
    """

    # Core content
    content: str = Field(..., description="Text content of the chunk")
    chunk_id: str = Field(..., description="Unique chunk identifier")

    # All stored properties (full dict for backward compatibility)
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="All stored properties from the vector database",
    )

    # Structured metadata
    metadata: RetrievalMetadata = Field(
        default_factory=RetrievalMetadata,
        description="Structured metadata extracted from properties",
    )


class SearchResultItem(RetrievalResultItem):
    """Search result item extending base retrieval result.

    Adds search-specific context: scores, retrieval method, and timestamp.
    This is used for results returned from search operations.
    """

    # Retrieval scores
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Similarity score (0.0-1.0)",
    )
    distance: Optional[float] = Field(
        default=None, description="Distance metric (for vector similarity)"
    )
    hybrid_score: Optional[float] = Field(
        default=None, description="Hybrid search score"
    )
    bm25_score: Optional[float] = Field(
        default=None, description="BM25 keyword search score"
    )

    # Retrieval context
    retrieval_method: Literal[
        "vector_similarity", "hybrid_search", "keyword_search"
    ] = Field(..., description="Method used for retrieval")
    retrieval_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when retrieval occurred",
    )

    # Convenience properties for email results
    @property
    def subject(self) -> Optional[str]:
        """Email subject (if applicable)."""
        return self.properties.get("email_subject") or self.metadata.email_subject

    @property
    def sender(self) -> Optional[str]:
        """Email sender (if applicable)."""
        return self.properties.get("email_sender") or self.metadata.email_sender

    @field_validator("retrieval_timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, v: Any) -> datetime:
        """Parse timestamp from string or datetime.

        Args:
            v: Timestamp value (datetime or ISO format string)

        Returns:
            datetime: Parsed datetime object

        Raises:
            ValueError: If the value cannot be parsed into a valid datetime
        """
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except (ValueError, AttributeError) as e:
                raise ValueError(
                    f"Invalid timestamp string format: {v}. "
                    f"Expected ISO 8601 format (e.g., '2024-01-15T14:30:00Z')."
                ) from e
        if v is None:
            raise ValueError(
                "retrieval_timestamp cannot be None. "
                "If not provided, it will default to the current time."
            )
        raise ValueError(
            f"Invalid timestamp type: {type(v).__name__}. "
            f"Expected datetime or ISO 8601 format string."
        )


class EmailMessageModel(BaseModel):
    """Pydantic model for email messages, compatible with EmailMessage dataclass.

    This model provides the same interface as EmailMessage but as a Pydantic
    model for better serialization, validation, and integration with other
    Pydantic-based APIs in the system.

    The model can be converted to/from EmailMessage dataclass for compatibility
    with EmailPreprocessor and other components that expect EmailMessage.
    """

    message_id: str = Field(..., description="Unique email message identifier")
    subject: str = Field(..., description="Email subject line")
    sender: EmailAddressDict = Field(
        ...,
        description="Email sender as dict with required 'email' and optional 'name'",
    )
    recipients: List[EmailAddressDict] = Field(
        default_factory=list,
        description="List of recipient email addresses as dicts",
    )
    cc_recipients: List[EmailAddressDict] = Field(
        default_factory=list, description="CC recipients as list of dicts"
    )
    bcc_recipients: List[EmailAddressDict] = Field(
        default_factory=list, description="BCC recipients as list of dicts"
    )
    body_text: Optional[str] = Field(default=None, description="Plain text email body")
    body_html: Optional[str] = Field(default=None, description="HTML email body")
    date_sent: Optional[datetime] = Field(default=None, description="Email send date")
    date_received: Optional[datetime] = Field(
        default=None, description="Email received date"
    )
    status: str = Field(
        default="unread", description="Email status (unread, read, draft, sent, trash)"
    )
    attachments: List[Dict[str, Any]] = Field(
        default_factory=list, description="Email attachments as list of dicts"
    )
    thread_id: Optional[str] = Field(default=None, description="Email thread ID")
    conversation_id: Optional[str] = Field(
        default=None, description="Email conversation ID"
    )
    folder: Optional[str] = Field(default=None, description="Email folder/path")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional email metadata"
    )

    def get_body(self) -> str:
        """Get the best available body content (HTML preferred, fallback to text).

        This method matches the EmailMessage.get_body() interface for compatibility.

        Returns:
            str: Email body content (HTML if available, otherwise text)
        """
        return self.body_html if self.body_html else (self.body_text or "")

    def get_all_recipients(self) -> List[EmailAddressDict]:
        """Get all recipients including CC and BCC.

        Returns:
            List of recipient dicts (recipients + cc_recipients + bcc_recipients)
        """
        return self.recipients + self.cc_recipients + self.bcc_recipients

    def to_email_message(self) -> "EmailMessage":
        """Convert EmailMessageModel to EmailMessage dataclass.

        Returns:
            EmailMessage: EmailMessage dataclass instance

        Raises:
            ImportError: If email_utils.models cannot be imported
        """

        # Convert sender dict to EmailAddress
        sender_addr = EmailAddress(
            email=self.sender["email"], name=self.sender.get("name")
        )

        # Convert recipients
        recipients_list = [
            EmailAddress(email=r["email"], name=r.get("name")) for r in self.recipients
        ]
        cc_list = [
            EmailAddress(email=r["email"], name=r.get("name"))
            for r in self.cc_recipients
        ]
        bcc_list = [
            EmailAddress(email=r["email"], name=r.get("name"))
            for r in self.bcc_recipients
        ]

        # Convert attachments
        attachments_list = []
        for att in self.attachments:
            attachments_list.append(
                EmailAttachment(
                    filename=att.get("filename", ""),
                    content_type=att.get("content_type", ""),
                    size=att.get("size", 0),
                    content=att.get("content"),
                    content_id=att.get("content_id"),
                )
            )

        # Convert status string to enum
        status_enum = MessageStatus.UNREAD
        if self.status:
            try:
                status_enum = MessageStatus(self.status.lower())
            except ValueError:
                status_enum = MessageStatus.UNREAD

        return EmailMessage(
            message_id=self.message_id,
            subject=self.subject,
            sender=sender_addr,
            recipients=recipients_list,
            cc_recipients=cc_list,
            bcc_recipients=bcc_list,
            body_text=self.body_text,
            body_html=self.body_html,
            date_sent=self.date_sent,
            date_received=self.date_received,
            status=status_enum,
            attachments=attachments_list,
            thread_id=self.thread_id,
            conversation_id=self.conversation_id,
            folder=self.folder,
            metadata=self.metadata,
        )

    @classmethod
    def from_email_message(cls, email: "EmailMessage") -> "EmailMessageModel":
        """Create EmailMessageModel from EmailMessage dataclass.

        Args:
            email: EmailMessage dataclass instance

        Returns:
            EmailMessageModel: EmailMessageModel Pydantic model instance
        """
        # Convert sender EmailAddress to dict
        sender_dict = {
            "email": email.sender.email,
            "name": email.sender.name,
        }

        # Convert recipients
        recipients_list = [{"email": r.email, "name": r.name} for r in email.recipients]
        cc_list = [{"email": r.email, "name": r.name} for r in email.cc_recipients]
        bcc_list = [{"email": r.email, "name": r.name} for r in email.bcc_recipients]

        # Convert attachments
        attachments_list = [
            {
                "filename": att.filename,
                "content_type": att.content_type,
                "size": att.size,
                "content": att.content,
                "content_id": att.content_id,
            }
            for att in email.attachments
        ]

        return cls(
            message_id=email.message_id,
            subject=email.subject,
            sender=sender_dict,
            recipients=recipients_list,
            cc_recipients=cc_list,
            bcc_recipients=bcc_list,
            body_text=email.body_text,
            body_html=email.body_html,
            date_sent=email.date_sent,
            date_received=email.date_received,
            status=email.status.value if email.status else "unread",
            attachments=attachments_list,
            thread_id=email.thread_id,
            conversation_id=email.conversation_id,
            folder=email.folder,
            metadata=email.metadata,
        )


class EmailListResult(BaseModel):
    """Container for email list results with metadata.

    Provides a structured container for email list results including
    the list of emails, count, folder searched, and execution metadata.
    Similar pattern to SearchResult for consistency.
    """

    emails: List[EmailMessageModel] = Field(
        default_factory=list, description="List of email items"
    )
    count: int = Field(..., ge=0, description="Total number of emails found")
    folder: Optional[str] = Field(
        default=None, description="Folder that was searched (None = all folders)"
    )
    execution_time: float = Field(..., ge=0.0, description="Execution time in seconds")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the email fetch operation",
    )

    @model_validator(mode="after")
    def validate_count_matches_emails(self) -> "EmailListResult":
        """Validate that count matches the actual number of emails.

        This ensures data consistency and prevents mismatched counts.
        """
        if self.count != len(self.emails):
            raise ValueError(
                f"Count ({self.count}) does not match the number of emails "
                f"({len(self.emails)})"
            )
        return self

    @property
    def email_messages(self) -> List["EmailMessage"]:
        """Convert EmailMessageModel list to EmailMessage list for compatibility.

        Returns:
            List[EmailMessage]: List of EmailMessage dataclass instances

        Raises:
            ImportError: If email_utils.models cannot be imported
        """
        return [email_item.to_email_message() for email_item in self.emails]
