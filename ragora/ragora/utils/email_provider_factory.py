"""Email utilities for the RAG system.

This module provides email functionality for creating databases from emails,
supporting multiple email providers through a unified interface. It's designed
to integrate seamlessly with the RAG system for email-based knowledge management.

## Features

- **Unified Interface**: Clean `EmailProvider` interface, supports multiple backends
- **Multiple Backends**: Support for IMAP/SMTP and Microsoft Graph API
- **Pluggable Architecture**: Easy to extend with new email providers
- **Type Safety**: Full type hints and comprehensive data models
- **RAG Integration**: Designed specifically for creating email databases for RAG systems

## Supported Providers

### IMAP/SMTP Provider
- Works with any IMAP/SMTP server (Gmail, Outlook, Exchange, etc.)
- Supports SSL/TLS connections
- Handles authentication, message fetching, and sending

### Microsoft Graph Provider
- Works with Microsoft 365, Outlook, and Exchange Online
- Uses OAuth2 authentication
- Full access to Microsoft Graph API features

## Quick Start

### Basic Usage

```python
from ragora.utils import EmailProviderFactory, ProviderType, IMAPCredentials

# Create IMAP credentials
credentials = IMAPCredentials(
    imap_server="imap.gmail.com",
    imap_port=993,
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    username="your-email@gmail.com",
    password="your-app-password"
)

# Create provider
provider = EmailProviderFactory.create_provider(ProviderType.IMAP, credentials)

# Connect and fetch messages
provider.connect()
messages = provider.fetch_messages(limit=10, unread_only=True)

# Process messages
for msg in messages:
    print(f"Subject: {msg.subject}")
    print(f"From: {msg.sender}")
    print(f"Body: {msg.get_body()}")

provider.disconnect()
```

### Microsoft Graph Usage

```python
from ragora.utils import EmailProviderFactory, ProviderType, GraphCredentials

# Create Graph credentials
credentials = GraphCredentials(
    client_id="your-client-id",
    client_secret="your-client-secret",
    tenant_id="your-tenant-id",
    access_token="your-access-token"
)

# Create provider
provider = EmailProviderFactory.create_provider(ProviderType.GRAPH, credentials)

# Connect and fetch messages
provider.connect()
messages = provider.fetch_messages(limit=10, folder="inbox")

# Create and send draft
draft = provider.create_draft(
    to=["recipient@example.com"],
    subject="Test Email",
    body="This is a test email from the RAG system."
)

provider.send_message(draft.draft_id)
provider.disconnect()
```

## API Reference

### EmailProviderFactory

The main factory class for creating email providers:

- `create_provider(provider_type, credentials)` - Create any provider type
- `create_imap_provider(...)` - Create IMAP provider with parameters
- `create_graph_provider(...)` - Create Graph provider with parameters
- `get_supported_providers()` - Get list of supported provider types

### EmailProvider Interface

All email providers implement this interface:

- `connect()` - Establish connection to email service
- `disconnect()` - Close connection to email service
- `fetch_messages(limit, folder, unread_only)` - Fetch messages from email service
- `fetch_message_by_id(message_id)` - Fetch a specific message by its ID
- `create_draft(to, subject, body, cc, bcc, attachments)` - Create a draft message
- `send_message(draft_id)` - Send a draft message
- `send_message_direct(...)` - Send a message directly without creating a draft
- `mark_as_read(message_id)` - Mark a message as read
- `get_folders()` - Get list of available folders
- `is_connected` - Check if connected to email service

### Data Models

- `EmailMessage` - Represents an email message with all metadata
- `EmailDraft` - Represents a draft email message
- `EmailAttachment` - Represents an email attachment
- `EmailAddress` - Represents an email address with optional display name
- `MessageStatus` - Enum for message status (UNREAD, READ, DRAFT, SENT, TRASH)
- `IMAPCredentials` - Credentials for IMAP/SMTP servers
- `GraphCredentials` - Credentials for Microsoft Graph API

## Configuration

### IMAP Credentials

```python
@dataclass
class IMAPCredentials:
    imap_server: str          # IMAP server hostname
    imap_port: int           # IMAP server port
    smtp_server: str         # SMTP server hostname
    smtp_port: int           # SMTP server port
    username: str            # Email username
    password: str            # Email password
    use_ssl: bool = True     # Use SSL for IMAP connection
    use_tls: bool = False    # Use TLS for IMAP connection
```

### Graph Credentials

```python
@dataclass
class GraphCredentials:
    client_id: str                    # Azure application client ID
    client_secret: str               # Azure application client secret
    tenant_id: str                   # Azure tenant ID
    access_token: Optional[str] = None    # Optional access token
    refresh_token: Optional[str] = None   # Optional refresh token
```

## Error Handling

The module provides comprehensive error handling:

- `ConnectionError`: Raised when connection to email service fails
- `AuthenticationError`: Raised when authentication fails
- `RuntimeError`: Raised for various operational errors

All providers handle errors gracefully and provide meaningful error messages.

## Dependencies

The email utilities module uses only standard library modules:

- `imaplib` - IMAP client
- `smtplib` - SMTP client
- `email` - Email parsing
- `requests` - HTTP client (for Graph API)
- `base64` - Encoding/decoding

No additional dependencies are required.

## Security Considerations

- Always use secure connections (SSL/TLS)
- Store credentials securely (environment variables, key vaults)
- Use app passwords for Gmail instead of account passwords
- Implement proper token refresh for OAuth2 flows
- Validate all input data before sending

## Testing

Run the comprehensive test suite:

```bash
pytest tests/unit/test_email_utils.py -v
```

The module includes full unit tests with proper mocking of external dependencies.

## License

This module is part of the ragora project and follows the same license terms.
"""

from enum import Enum
from typing import Union

from .email_utils.base import EmailProvider
from .email_utils.graph_provider import GraphProvider
from .email_utils.imap_provider import IMAPProvider
from .email_utils.models import GraphCredentials, IMAPCredentials


class ProviderType(Enum):
    """Supported email provider types."""

    IMAP = "imap"
    GRAPH = "graph"


class EmailProviderFactory:
    """Factory class for creating email providers."""

    @staticmethod
    def create_provider(
        provider_type: Union[ProviderType, str],
        credentials: Union[IMAPCredentials, GraphCredentials],
    ) -> EmailProvider:
        """Create an email provider instance.

        Args:
            provider_type: Type of provider to create (ProviderType enum or string)
            credentials: Provider-specific credentials

        Returns:
            EmailProvider instance

        Raises:
            ValueError: If provider type is not supported
            TypeError: If credentials type doesn't match provider type
        """
        # Normalize provider type
        if isinstance(provider_type, str):
            try:
                provider_type = ProviderType(provider_type.lower())
            except ValueError:
                raise ValueError(f"Unsupported provider type: {provider_type}")

        # Validate credentials match provider type
        if provider_type == ProviderType.IMAP:
            if not isinstance(credentials, IMAPCredentials):
                raise TypeError("IMAP provider requires IMAPCredentials")
            return IMAPProvider(credentials)

        elif provider_type == ProviderType.GRAPH:
            if not isinstance(credentials, GraphCredentials):
                raise TypeError("Graph provider requires GraphCredentials")
            return GraphProvider(credentials)

        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")

    @staticmethod
    def create_imap_provider(
        imap_server: str,
        imap_port: int,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        use_ssl: bool = True,
        use_tls: bool = False,
    ) -> IMAPProvider:
        """Create an IMAP provider with the given configuration.

        Args:
            imap_server: IMAP server hostname
            imap_port: IMAP server port
            smtp_server: SMTP server hostname
            smtp_port: SMTP server port
            username: Email username
            password: Email password
            use_ssl: Whether to use SSL for IMAP connection
            use_tls: Whether to use TLS for IMAP connection

        Returns:
            IMAPProvider instance
        """
        credentials = IMAPCredentials(
            imap_server=imap_server,
            imap_port=imap_port,
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            username=username,
            password=password,
            use_ssl=use_ssl,
            use_tls=use_tls,
        )
        return IMAPProvider(credentials)

    @staticmethod
    def create_graph_provider(
        client_id: str,
        client_secret: str,
        tenant_id: str,
        access_token: str = None,
        refresh_token: str = None,
    ) -> GraphProvider:
        """Create a Microsoft Graph provider with the given configuration.

        Args:
            client_id: Azure application client ID
            client_secret: Azure application client secret
            tenant_id: Azure tenant ID
            access_token: Optional access token (if not provided, will use client credentials)
            refresh_token: Optional refresh token

        Returns:
            GraphProvider instance
        """
        credentials = GraphCredentials(
            client_id=client_id,
            client_secret=client_secret,
            tenant_id=tenant_id,
            access_token=access_token,
            refresh_token=refresh_token,
        )
        return GraphProvider(credentials)

    @staticmethod
    def get_supported_providers() -> list[str]:
        """Get list of supported provider types.

        Returns:
            List of supported provider type names
        """
        return [provider.value for provider in ProviderType]
