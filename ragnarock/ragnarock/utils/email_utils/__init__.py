"""Email utilities for the RAG system.

This module provides email functionality for creating databases from emails,
supporting multiple email providers through a unified interface.
"""

from .base import EmailProvider
from .graph_provider import GraphProvider
from .imap_provider import IMAPProvider
from .models import EmailAttachment, EmailDraft, EmailMessage

__all__ = [
    "EmailMessage",
    "EmailDraft",
    "EmailAttachment",
    "EmailProvider",
    "IMAPProvider",
    "GraphProvider",
]
