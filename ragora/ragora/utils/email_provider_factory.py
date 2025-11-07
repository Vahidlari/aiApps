"""Factory helpers for creating email provider implementations."""

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
    """Factory for constructing concrete email providers.

    Examples:
        ```python
        provider = EmailProviderFactory.create_provider(
            ProviderType.IMAP,
            IMAPCredentials(
                imap_server="imap.example.com",
                imap_port=993,
                smtp_server="smtp.example.com",
                smtp_port=587,
                username="user",
                password="pass",
            ),
        )
        provider.connect()
        ```
    """

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
            EmailProvider: Concrete provider instance.

        Raises:
            ValueError: If the provider type is unsupported.
            TypeError: If the provided credentials do not match the provider type.

        Examples:
            ```python
            provider = EmailProviderFactory.create_provider(
                ProviderType.IMAP,
                IMAPCredentials(
                    imap_server="imap.example.com",
                    imap_port=993,
                    smtp_server="smtp.example.com",
                    smtp_port=587,
                    username="user",
                    password="pass",
                ),
            )
            ```
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
            IMAPProvider: Configured provider instance.

        Examples:
            ```python
            provider = EmailProviderFactory.create_imap_provider(
                imap_server="imap.example.com",
                imap_port=993,
                smtp_server="smtp.example.com",
                smtp_port=587,
                username="user",
                password="pass",
            )
            ```
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
            GraphProvider: Configured provider instance.

        Examples:
            ```python
            provider = EmailProviderFactory.create_graph_provider(
                client_id="app-id",
                client_secret="secret",
                tenant_id="tenant",
            )
            ```
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
