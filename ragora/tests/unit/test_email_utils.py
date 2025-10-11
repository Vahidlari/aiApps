"""Unit tests for email utilities."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from ragora.utils.email_provider_factory import EmailProviderFactory, ProviderType
from ragora.utils.email_utils.base import EmailProvider
from ragora.utils.email_utils.graph_provider import AuthenticationError, GraphProvider
from ragora.utils.email_utils.imap_provider import IMAPProvider
from ragora.utils.email_utils.models import (
    EmailAddress,
    EmailAttachment,
    EmailDraft,
    EmailMessage,
    GraphCredentials,
    IMAPCredentials,
    MessageStatus,
)


class TestEmailModels:
    """Test email data models."""

    def test_email_address_creation(self):
        """Test EmailAddress creation and string representation."""
        addr1 = EmailAddress("test@example.com")
        assert addr1.email == "test@example.com"
        assert addr1.name is None
        assert str(addr1) == "test@example.com"

        addr2 = EmailAddress("test@example.com", "Test User")
        assert addr2.email == "test@example.com"
        assert addr2.name == "Test User"
        assert str(addr2) == "Test User <test@example.com>"

    def test_email_message_creation(self):
        """Test EmailMessage creation and methods."""
        sender = EmailAddress("sender@example.com", "Sender")
        recipients = [EmailAddress("recipient@example.com", "Recipient")]

        msg = EmailMessage(
            message_id="msg123",
            subject="Test Subject",
            sender=sender,
            recipients=recipients,
            body_text="Test body",
            body_html="<p>Test body</p>",
        )

        assert msg.message_id == "msg123"
        assert msg.subject == "Test Subject"
        assert msg.get_body() == "<p>Test body</p>"  # HTML preferred
        assert len(msg.get_all_recipients()) == 1

    def test_email_draft_creation(self):
        """Test EmailDraft creation and methods."""
        recipients = [EmailAddress("recipient@example.com")]

        draft = EmailDraft(
            draft_id="draft123",
            subject="Test Subject",
            recipients=recipients,
            body_text="Test body",
        )

        assert draft.draft_id == "draft123"
        assert draft.get_body() == "Test body"
        assert len(draft.get_all_recipients()) == 1

    def test_email_attachment_creation(self):
        """Test EmailAttachment creation."""
        content = b"test content"
        attachment = EmailAttachment(
            filename="test.txt", content_type="text/plain", size=12, content=content
        )

        assert attachment.filename == "test.txt"
        assert attachment.content_type == "text/plain"
        assert attachment.size == 12
        assert attachment.content == content

    def test_imap_credentials_creation(self):
        """Test IMAPCredentials creation."""
        creds = IMAPCredentials(
            imap_server="imap.example.com",
            imap_port=993,
            smtp_server="smtp.example.com",
            smtp_port=587,
            username="user@example.com",
            password="password",
        )

        assert creds.imap_server == "imap.example.com"
        assert creds.imap_port == 993
        assert creds.use_ssl is True  # Default value

    def test_graph_credentials_creation(self):
        """Test GraphCredentials creation."""
        creds = GraphCredentials(
            client_id="client123", client_secret="secret123", tenant_id="tenant123"
        )

        assert creds.client_id == "client123"
        assert creds.client_secret == "secret123"
        assert creds.tenant_id == "tenant123"
        assert creds.access_token is None  # Default value


class TestIMAPProvider:
    """Test IMAP provider implementation."""

    @pytest.fixture
    def imap_credentials(self):
        """Create IMAP credentials for testing."""
        return IMAPCredentials(
            imap_server="imap.example.com",
            imap_port=993,
            smtp_server="smtp.example.com",
            smtp_port=587,
            username="test@example.com",
            password="password",
        )

    @pytest.fixture
    def imap_provider(self, imap_credentials):
        """Create IMAP provider for testing."""
        return IMAPProvider(imap_credentials)

    def test_imap_provider_initialization(self, imap_provider, imap_credentials):
        """Test IMAP provider initialization."""
        assert imap_provider.credentials == imap_credentials
        assert not imap_provider.is_connected

    @patch("ragora.utils.email_utils.imap_provider.imaplib.IMAP4_SSL")
    @patch("ragora.utils.email_utils.imap_provider.smtplib.SMTP_SSL")
    def test_imap_connect(self, mock_smtp, mock_imap, imap_provider):
        """Test IMAP provider connection."""
        mock_imap_instance = Mock()
        mock_smtp_instance = Mock()
        mock_imap.return_value = mock_imap_instance
        mock_smtp.return_value = mock_smtp_instance

        imap_provider.connect()

        assert imap_provider.is_connected
        mock_imap_instance.login.assert_called_once()
        mock_smtp_instance.login.assert_called_once()

    def test_imap_disconnect(self, imap_provider):
        """Test IMAP provider disconnection."""
        # Mock the clients
        imap_provider._imap_client = Mock()
        imap_provider._smtp_client = Mock()
        imap_provider._connected = True

        imap_provider.disconnect()

        assert not imap_provider.is_connected
        assert imap_provider._imap_client is None
        assert imap_provider._smtp_client is None

    def test_imap_parse_address(self, imap_provider):
        """Test address parsing."""
        # Test simple email
        addr = imap_provider._parse_address("test@example.com")
        assert addr.email == "test@example.com"
        assert addr.name is None

        # Test email with name
        addr = imap_provider._parse_address("Test User <test@example.com>")
        assert addr.email == "test@example.com"
        assert addr.name == "Test User"

    def test_imap_parse_address_list(self, imap_provider):
        """Test address list parsing."""
        addresses = imap_provider._parse_address_list(
            "test1@example.com, Test User <test2@example.com>"
        )
        assert len(addresses) == 2
        assert addresses[0].email == "test1@example.com"
        assert addresses[1].email == "test2@example.com"
        assert addresses[1].name == "Test User"


class TestGraphProvider:
    """Test Microsoft Graph provider implementation."""

    @pytest.fixture
    def graph_credentials(self):
        """Create Graph credentials for testing."""
        return GraphCredentials(
            client_id="client123",
            client_secret="secret123",
            tenant_id="tenant123",
            access_token="access_token_123",
        )

    @pytest.fixture
    def graph_provider(self, graph_credentials):
        """Create Graph provider for testing."""
        return GraphProvider(graph_credentials)

    def test_graph_provider_initialization(self, graph_provider, graph_credentials):
        """Test Graph provider initialization."""
        assert graph_provider.credentials == graph_credentials
        assert not graph_provider.is_connected

    @patch("ragora.utils.email_utils.graph_provider.requests.get")
    def test_graph_connect_with_token(self, mock_get, graph_provider):
        """Test Graph provider connection with existing token."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        graph_provider.connect()

        assert graph_provider.is_connected
        assert graph_provider._access_token == "access_token_123"

    @patch("ragora.utils.email_utils.graph_provider.requests.post")
    def test_graph_connect_without_token(self, mock_post):
        """Test Graph provider connection without existing token."""
        credentials = GraphCredentials(
            client_id="client123", client_secret="secret123", tenant_id="tenant123"
        )
        provider = GraphProvider(credentials)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "new_token_123"}
        mock_post.return_value = mock_response

        provider.connect()

        assert provider.is_connected
        assert provider._access_token == "new_token_123"

    def test_graph_parse_date(self, graph_provider):
        """Test Graph date parsing."""
        # Test valid date
        date_str = "2023-12-01T10:30:00Z"
        parsed_date = graph_provider._parse_graph_date(date_str)
        assert parsed_date is not None
        assert isinstance(parsed_date, datetime)

        # Test None date
        assert graph_provider._parse_graph_date(None) is None

        # Test invalid date
        assert graph_provider._parse_graph_date("invalid_date") is None

    def test_graph_parse_attachments(self, graph_provider):
        """Test Graph attachments parsing."""
        attachments_data = [
            {
                "name": "test.txt",
                "contentType": "text/plain",
                "size": 12,
                "contentBytes": "dGVzdCBjb250ZW50",
            }
        ]

        attachments = graph_provider._parse_graph_attachments(attachments_data)

        assert len(attachments) == 1
        assert attachments[0].filename == "test.txt"
        assert attachments[0].content_type == "text/plain"
        assert attachments[0].size == 12
        assert attachments[0].content == b"test content"


class TestEmailProviderFactory:
    """Test email provider factory."""

    def test_create_provider_with_enum(self):
        """Test creating provider with ProviderType enum."""
        credentials = IMAPCredentials(
            imap_server="imap.example.com",
            imap_port=993,
            smtp_server="smtp.example.com",
            smtp_port=587,
            username="test@example.com",
            password="password",
        )

        provider = EmailProviderFactory.create_provider(ProviderType.IMAP, credentials)
        assert isinstance(provider, IMAPProvider)

    def test_create_provider_with_string(self):
        """Test creating provider with string type."""
        credentials = GraphCredentials(
            client_id="client123", client_secret="secret123", tenant_id="tenant123"
        )

        provider = EmailProviderFactory.create_provider("graph", credentials)
        assert isinstance(provider, GraphProvider)

    def test_create_provider_invalid_type(self):
        """Test creating provider with invalid type."""
        credentials = IMAPCredentials(
            imap_server="imap.example.com",
            imap_port=993,
            smtp_server="smtp.example.com",
            smtp_port=587,
            username="test@example.com",
            password="password",
        )

        with pytest.raises(ValueError):
            EmailProviderFactory.create_provider("invalid", credentials)

    def test_create_provider_wrong_credentials(self):
        """Test creating provider with wrong credentials type."""
        credentials = IMAPCredentials(
            imap_server="imap.example.com",
            imap_port=993,
            smtp_server="smtp.example.com",
            smtp_port=587,
            username="test@example.com",
            password="password",
        )

        with pytest.raises(TypeError):
            EmailProviderFactory.create_provider(ProviderType.GRAPH, credentials)

    def test_create_imap_provider(self):
        """Test creating IMAP provider directly."""
        provider = EmailProviderFactory.create_imap_provider(
            imap_server="imap.example.com",
            imap_port=993,
            smtp_server="smtp.example.com",
            smtp_port=587,
            username="test@example.com",
            password="password",
        )

        assert isinstance(provider, IMAPProvider)
        assert provider.credentials.imap_server == "imap.example.com"

    def test_create_graph_provider(self):
        """Test creating Graph provider directly."""
        provider = EmailProviderFactory.create_graph_provider(
            client_id="client123", client_secret="secret123", tenant_id="tenant123"
        )

        assert isinstance(provider, GraphProvider)
        assert provider.credentials.client_id == "client123"

    def test_get_supported_providers(self):
        """Test getting supported provider types."""
        providers = EmailProviderFactory.get_supported_providers()
        assert "imap" in providers
        assert "graph" in providers


class TestIntegration:
    """Integration tests for email utilities."""

    def test_email_workflow_simulation(self):
        """Test a complete email workflow simulation."""
        # Create credentials
        credentials = IMAPCredentials(
            imap_server="imap.example.com",
            imap_port=993,
            smtp_server="smtp.example.com",
            smtp_port=587,
            username="test@example.com",
            password="password",
        )

        # Create provider
        provider = EmailProviderFactory.create_provider(ProviderType.IMAP, credentials)

        # Verify provider type
        assert isinstance(provider, IMAPProvider)

        # Test draft creation (without actual connection)
        # Mock the _connected attribute instead of the property
        with patch.object(provider, "_connected", True):
            draft = provider.create_draft(
                to=["recipient@example.com"], subject="Test Subject", body="Test body"
            )

            assert draft.subject == "Test Subject"
            assert len(draft.recipients) == 1
            assert draft.recipients[0].email == "recipient@example.com"


if __name__ == "__main__":
    pytest.main([__file__])
