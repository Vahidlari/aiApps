"""Microsoft Graph API email provider implementation."""

import base64
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests

from .base import EmailProvider
from .models import (
    EmailAddress,
    EmailAttachment,
    EmailDraft,
    EmailMessage,
    GraphCredentials,
    MessageStatus,
)


class GraphProvider(EmailProvider):
    """Microsoft Graph API email provider for Outlook/Office 365."""

    BASE_URL = "https://graph.microsoft.com/v1.0"

    def __init__(self, credentials: GraphCredentials):
        """Initialize Graph provider with credentials.

        Args:
            credentials: Microsoft Graph API credentials
        """
        super().__init__(credentials)
        self._access_token: Optional[str] = None
        self._connected = False

    def connect(self) -> None:
        """Establish connection to Microsoft Graph API."""
        try:
            if self.credentials.access_token:
                # Use provided access token
                self._access_token = self.credentials.access_token
                # Verify token is valid
                if self._verify_token():
                    self._connected = True
                    return
                else:
                    raise AuthenticationError("Invalid access token")
            else:
                # Get access token using client credentials flow
                self._get_access_token()
                self._connected = True

        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to Microsoft Graph: {str(e)}")

    def disconnect(self) -> None:
        """Close connection to Microsoft Graph API."""
        self._access_token = None
        self._connected = False

    def _get_access_token(self) -> None:
        """Get access token using client credentials flow."""
        token_url = f"https://login.microsoftonline.com/{self.credentials.tenant_id}/oauth2/v2.0/token"

        data = {
            "client_id": self.credentials.client_id,
            "client_secret": self.credentials.client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        }

        response = requests.post(token_url, data=data)
        response.raise_for_status()

        token_data = response.json()
        self._access_token = token_data["access_token"]

    def _verify_token(self) -> bool:
        """Verify if the access token is valid."""
        if not self._access_token:
            return False

        try:
            headers = {"Authorization": f"Bearer {self._access_token}"}
            response = requests.get(f"{self.BASE_URL}/me", headers=headers)
            return response.status_code == 200
        except Exception:
            return False

    def _make_request(
        self, method: str, endpoint: str, data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make authenticated request to Microsoft Graph API.
        Args:
            method: The HTTP method to use
            endpoint: The endpoint to request
            data: The data to send with the request
        Returns:
            Dictionary containing the response data
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to Microsoft Graph")

        url = urljoin(self.BASE_URL, endpoint)
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == "PATCH":
                response = requests.patch(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()

            if response.content:
                return response.json()
            return {}

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Graph API request failed: {str(e)}")

    def fetch_messages(
        self, limit: int = 50, folder: Optional[str] = None, unread_only: bool = False
    ) -> List[EmailMessage]:
        """Fetch messages from Microsoft Graph API.
        Args:
            limit: The maximum number of messages to fetch
            folder: The folder to search for messages
            unread_only: Whether to only fetch unread messages
        Returns:
            List of EmailMessage objects
        """
        try:
            # Build endpoint
            if folder:
                endpoint = f"/me/mailFolders/{folder}/messages"
            else:
                endpoint = "/me/messages"

            # Add query parameters
            params = []
            if limit > 0:
                params.append(f"$top={limit}")

            if unread_only:
                params.append("$filter=isRead eq false")

            # Add ordering
            params.append("$orderby=receivedDateTime desc")

            if params:
                endpoint += "?" + "&".join(params)

            response = self._make_request("GET", endpoint)
            messages_data = response.get("value", [])

            email_messages = []
            for msg_data in messages_data:
                try:
                    email_msg = self._parse_graph_message(msg_data)
                    if email_msg:
                        email_messages.append(email_msg)
                except Exception:
                    # Skip problematic messages
                    continue

            return email_messages

        except Exception as e:
            raise RuntimeError(f"Failed to fetch messages: {str(e)}")

    def fetch_message_by_id(self, message_id: str) -> Optional[EmailMessage]:
        """Fetch a specific message by its ID.
        Args:
            message_id: The ID of the message to fetch
        Returns:
            EmailMessage object if the message was found, None otherwise
        """
        try:
            endpoint = f"/me/messages/{message_id}"
            response = self._make_request("GET", endpoint)

            return self._parse_graph_message(response)

        except Exception as e:
            if "404" in str(e):
                return None
            raise RuntimeError(f"Failed to fetch message {message_id}: {str(e)}")

    def _parse_graph_message(self, msg_data: Dict[str, Any]) -> Optional[EmailMessage]:
        """Parse Microsoft Graph message data into EmailMessage object.
        Args:
            msg_data: The message data to parse
        Returns:
            EmailMessage object if the message was found, None otherwise
        """
        try:
            # Extract basic fields
            message_id = msg_data.get("id", "")
            subject = msg_data.get("subject", "")

            # Parse sender
            sender_info = msg_data.get("from", {})
            sender = EmailAddress(
                email=sender_info.get("emailAddress", {}).get("address", ""),
                name=sender_info.get("emailAddress", {}).get("name", ""),
            )

            # Parse recipients
            to_recipients = []
            for recipient in msg_data.get("toRecipients", []):
                to_recipients.append(
                    EmailAddress(
                        email=recipient.get("emailAddress", {}).get("address", ""),
                        name=recipient.get("emailAddress", {}).get("name", ""),
                    )
                )

            cc_recipients = []
            for recipient in msg_data.get("ccRecipients", []):
                cc_recipients.append(
                    EmailAddress(
                        email=recipient.get("emailAddress", {}).get("address", ""),
                        name=recipient.get("emailAddress", {}).get("name", ""),
                    )
                )

            bcc_recipients = []
            for recipient in msg_data.get("bccRecipients", []):
                bcc_recipients.append(
                    EmailAddress(
                        email=recipient.get("emailAddress", {}).get("address", ""),
                        name=recipient.get("emailAddress", {}).get("name", ""),
                    )
                )

            # Parse dates
            date_sent = self._parse_graph_date(msg_data.get("sentDateTime"))
            date_received = self._parse_graph_date(msg_data.get("receivedDateTime"))

            # Extract body
            body = msg_data.get("body", {})
            body_text = (
                body.get("content", "") if body.get("contentType") == "text" else None
            )
            body_html = (
                body.get("content", "") if body.get("contentType") == "html" else None
            )

            # Parse status
            status = (
                MessageStatus.READ
                if msg_data.get("isRead", False)
                else MessageStatus.UNREAD
            )

            # Parse attachments
            attachments = self._parse_graph_attachments(msg_data.get("attachments", []))

            # Get folder information
            parent_folder_id = msg_data.get("parentFolderId", "")

            return EmailMessage(
                message_id=message_id,
                subject=subject,
                sender=sender,
                recipients=to_recipients,
                cc_recipients=cc_recipients,
                bcc_recipients=bcc_recipients,
                body_text=body_text,
                body_html=body_html,
                date_sent=date_sent,
                date_received=date_received,
                status=status,
                attachments=attachments,
                folder=parent_folder_id,
                metadata=msg_data,
            )

        except Exception:
            return None

    def _parse_graph_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse Microsoft Graph date string.
        Args:
            date_str: The date string to parse
        Returns:
            datetime object if the date was parsed successfully, None otherwise
        """
        if not date_str:
            return None

        try:
            # Graph API returns ISO 8601 format
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return None

    def _parse_graph_attachments(
        self, attachments_data: List[Dict[str, Any]]
    ) -> List[EmailAttachment]:
        """Parse Microsoft Graph attachments.
        Args:
            attachments_data: The attachments data to parse
        Returns:
            List of EmailAttachment objects
        """
        attachments = []

        for attachment_data in attachments_data:
            try:
                filename = attachment_data.get("name", "")
                content_type = attachment_data.get(
                    "contentType", "application/octet-stream"
                )
                size = attachment_data.get("size", 0)

                # Get attachment content if available
                content = None
                if "contentBytes" in attachment_data:
                    content = base64.b64decode(attachment_data["contentBytes"])

                attachments.append(
                    EmailAttachment(
                        filename=filename,
                        content_type=content_type,
                        size=size,
                        content=content,
                        content_id=attachment_data.get("contentId"),
                    )
                )

            except Exception:
                # Skip problematic attachments
                continue

        return attachments

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
        """Create a draft message using Microsoft Graph API.
        Args:
            to: List of recipient email addresses
            subject: Email subject line
            body: Email body content (HTML or plain text)
            cc: Optional list of CC recipient email addresses
            bcc: Optional list of BCC recipient email addresses
            attachments: Optional list of attachment file paths
            folder: The folder to save the draft message
        Returns:
            EmailDraft object
        """
        try:
            # Prepare message data
            message_data = {
                "subject": subject,
                "body": {
                    "contentType": "text" if not body.startswith("<") else "html",
                    "content": body,
                },
                "toRecipients": [{"emailAddress": {"address": addr}} for addr in to],
            }

            if cc:
                message_data["ccRecipients"] = [
                    {"emailAddress": {"address": addr}} for addr in cc
                ]

            if bcc:
                message_data["bccRecipients"] = [
                    {"emailAddress": {"address": addr}} for addr in bcc
                ]

            # Create draft
            response = self._make_request("POST", "/me/messages", message_data)

            # Save as draft
            draft_response = self._make_request(
                "POST", f"/me/messages/{response['id']}/save", {}
            )

            draft_id = response["id"]

            # Parse recipients
            to_addresses = [EmailAddress(addr) for addr in to]
            cc_addresses = [EmailAddress(addr) for addr in (cc or [])]
            bcc_addresses = [EmailAddress(addr) for addr in (bcc or [])]

            # Process attachments
            email_attachments = []
            if attachments:
                for file_path in attachments:
                    try:
                        with open(file_path, "rb") as f:
                            content = f.read()

                        attachment_data = {
                            "@odata.type": "#microsoft.graph.fileAttachment",
                            "name": file_path.split("/")[-1],
                            "contentType": "application/octet-stream",
                            "contentBytes": base64.b64encode(content).decode("utf-8"),
                        }

                        # Add attachment to draft
                        self._make_request(
                            "POST",
                            f"/me/messages/{draft_id}/attachments",
                            attachment_data,
                        )

                        email_attachments.append(
                            EmailAttachment(
                                filename=file_path.split("/")[-1],
                                content_type="application/octet-stream",
                                size=len(content),
                                content=content,
                            )
                        )

                    except Exception:
                        # Skip problematic attachments
                        continue

            return EmailDraft(
                draft_id=draft_id,
                subject=subject,
                recipients=to_addresses,
                cc_recipients=cc_addresses,
                bcc_recipients=bcc_addresses,
                body_text=body,
                attachments=email_attachments,
                created_date=datetime.now(),
                modified_date=datetime.now(),
                metadata=response,
            )

        except Exception as e:
            raise RuntimeError(f"Failed to create draft: {str(e)}")

    def send_message(self, draft_id: str, folder: str = "Drafts") -> bool:
        """Send a draft message.
        Args:
            draft_id: The ID of the draft message to send
            folder: The folder to search for the draft message
        Returns:
            True if the draft message was sent successfully, False otherwise
        """
        try:
            self._make_request("POST", f"/me/messages/{draft_id}/send")
            return True

        except Exception as e:
            raise RuntimeError(f"Failed to send message: {str(e)}")

    def send_message_direct(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
    ) -> bool:
        """Send a message directly via Microsoft Graph API.
        Args:
            to: List of recipient email addresses
            subject: Email subject line
            body: Email body content (HTML or plain text)
            cc: Optional list of CC recipient email addresses
            bcc: Optional list of BCC recipient email addresses
            attachments: Optional list of attachment file paths
        Returns:
            True if the message was sent successfully, False otherwise
        """
        try:
            # Create draft first
            draft = self.create_draft(to, subject, body, cc, bcc, attachments)

            # Send the draft
            return self.send_message(draft.draft_id)

        except Exception as e:
            raise RuntimeError(f"Failed to send message directly: {str(e)}")

    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read.
        Args:
            message_id: The ID of the message to mark as read
        Returns:
            True if the message was marked as read successfully, False otherwise
        """
        try:
            update_data = {"isRead": True}
            self._make_request("PATCH", f"/me/messages/{message_id}", update_data)
            return True

        except Exception as e:
            if "404" in str(e):
                return False
            raise RuntimeError(f"Failed to mark message as read: {str(e)}")

    def get_folders(self) -> List[str]:
        """Get list of available folders.
        Returns:
            List of available folders
        """
        try:
            response = self._make_request("GET", "/me/mailFolders")
            folders_data = response.get("value", [])

            folders = []
            for folder_data in folders_data:
                folders.append(folder_data.get("displayName", ""))

            return folders

        except Exception as e:
            raise RuntimeError(f"Failed to get folders: {str(e)}")

    @property
    def is_connected(self) -> bool:
        """Check if connected to Microsoft Graph API.
        Returns:
            True if connected to Microsoft Graph API, False otherwise
        """
        return self._connected and self._access_token is not None


class AuthenticationError(Exception):
    """Raised when authentication fails.
    Args:
        message: The error message
    """

    pass
