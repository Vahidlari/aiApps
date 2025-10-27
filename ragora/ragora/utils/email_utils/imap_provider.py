"""IMAP/SMTP email provider implementation."""

import email
import imaplib
import os
import smtplib
from datetime import datetime
from email.header import decode_header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional

from .base import EmailProvider
from .models import (
    EmailAddress,
    EmailAttachment,
    EmailDraft,
    EmailMessage,
    IMAPCredentials,
    MessageStatus,
)


class IMAPProvider(EmailProvider):
    """IMAP/SMTP email provider for generic email servers."""

    def __init__(self, credentials: IMAPCredentials):
        """Initialize IMAP provider with credentials.

        Args:
            credentials: IMAP/SMTP server credentials
        """
        super().__init__(credentials)
        self._imap_client: Optional[imaplib.IMAP4_SSL] = None
        self._smtp_client: Optional[smtplib.SMTP] = None
        self._connected = False

    def connect(self) -> None:
        """Establish connection to IMAP and SMTP servers."""
        try:
            # Connect to IMAP server
            if self.credentials.use_ssl:
                self._imap_client = imaplib.IMAP4_SSL(
                    self.credentials.imap_server, self.credentials.imap_port
                )
            else:
                self._imap_client = imaplib.IMAP4(
                    self.credentials.imap_server, self.credentials.imap_port
                )
                if self.credentials.use_tls:
                    self._imap_client.starttls()

            # Login to IMAP
            self._imap_client.login(
                self.credentials.username, self.credentials.password
            )

            # Connect to SMTP server
            if self.credentials.use_ssl:
                self._smtp_client = smtplib.SMTP_SSL(
                    self.credentials.smtp_server, self.credentials.smtp_port
                )
            else:
                self._smtp_client = smtplib.SMTP(
                    self.credentials.smtp_server, self.credentials.smtp_port
                )
                if self.credentials.use_tls:
                    self._smtp_client.starttls()

            self._smtp_client.login(
                self.credentials.username, self.credentials.password
            )

            self._connected = True

        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to email servers: {str(e)}")

    def disconnect(self) -> None:
        """Close connections to IMAP and SMTP servers."""
        try:
            if self._imap_client:
                self._imap_client.close()
                self._imap_client.logout()
                self._imap_client = None

            if self._smtp_client:
                self._smtp_client.quit()
                self._smtp_client = None

            self._connected = False

        except Exception:
            # Ignore errors during disconnect
            pass

    def fetch_messages(
        self,
        limit: Optional[int] = None,
        folder: Optional[str] = None,
        unread_only: bool = False,
    ) -> List[EmailMessage]:
        """Fetch messages from IMAP server.
        Args:
            limit: The maximum number of messages to fetch
            folder: The folder to search for messages
            unread_only: Whether to only fetch unread messages
        Returns:
            List of EmailMessage objects
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to IMAP server")

        try:
            # Select folder (default to INBOX)
            folder_name = folder or "INBOX"
            self._imap_client.select(folder_name)

            # Build search criteria
            search_criteria = "ALL"
            if unread_only:
                search_criteria = "UNSEEN"

            # Search for messages
            status, messages = self._imap_client.search(None, search_criteria)
            if status != "OK":
                raise RuntimeError("Failed to search messages")

            message_ids = messages[0].split()
            message_ids = (
                message_ids[-limit:] if limit is not None and limit > 0 else message_ids
            )

            email_messages = []
            for msg_id in message_ids:
                try:
                    email_msg = self._fetch_single_message(msg_id)
                    if email_msg:
                        email_messages.append(email_msg)
                except Exception as e:
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
        if not self.is_connected:
            raise ConnectionError("Not connected to IMAP server")

        try:
            # Search for the specific message ID
            status, messages = self._imap_client.search(
                None, f'HEADER Message-ID "{message_id}"'
            )
            if status != "OK" or not messages[0]:
                return None

            msg_ids = messages[0].split()
            if not msg_ids:
                return None

            return self._fetch_single_message(msg_ids[0])

        except Exception as e:
            raise RuntimeError(f"Failed to fetch message {message_id}: {str(e)}")

    def _fetch_single_message(self, msg_id: bytes) -> Optional[EmailMessage]:
        """Fetch and parse a single message.
        Args:
            msg_id: The ID of the message to fetch
        Returns:
            EmailMessage object if the message was found, None otherwise
        """
        try:
            status, msg_data = self._imap_client.fetch(msg_id, "(RFC822)")
            if status != "OK":
                return None

            raw_email = msg_data[0][1]
            email_message = email.message_from_bytes(raw_email)

            return self._parse_email_message(email_message, msg_id.decode())

        except Exception:
            return None

    def _parse_email_message(
        self, email_msg: email.message.Message, msg_id: str
    ) -> EmailMessage:
        """Parse email.message.Message into EmailMessage object.
        Args:
            email_msg: The email.message.Message object to parse
            msg_id: The ID of the message
        Returns:
            EmailMessage object
        """
        # Extract headers
        subject = self._decode_header(email_msg.get("Subject", ""))
        sender = self._parse_address(email_msg.get("From", ""))

        # Parse recipients
        to_addresses = self._parse_address_list(email_msg.get("To", ""))
        cc_addresses = self._parse_address_list(email_msg.get("Cc", ""))
        bcc_addresses = self._parse_address_list(email_msg.get("Bcc", ""))

        # Parse dates
        date_sent = self._parse_date(email_msg.get("Date"))

        # Extract body
        body_text, body_html = self._extract_body(email_msg)

        # Extract attachments
        attachments = self._extract_attachments(email_msg)

        # Determine status
        status = MessageStatus.READ if email_msg.get("X-Seen") else MessageStatus.UNREAD

        return EmailMessage(
            message_id=email_msg.get("Message-ID", msg_id),
            subject=subject,
            sender=sender,
            recipients=to_addresses,
            cc_recipients=cc_addresses,
            bcc_recipients=bcc_addresses,
            body_text=body_text,
            body_html=body_html,
            date_sent=date_sent,
            date_received=datetime.now(),
            status=status,
            attachments=attachments,
        )

    def _decode_header(self, header: str) -> str:
        """Decode email header.
        Args:
            header: The email header to decode
        Returns:
            Decoded email header
        """
        if not header:
            return ""

        decoded_parts = decode_header(header)
        decoded_string = ""

        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    decoded_string += part.decode(encoding)
                else:
                    decoded_string += part.decode("utf-8", errors="ignore")
            else:
                decoded_string += part

        return decoded_string

    def _parse_address(self, address_str: str) -> EmailAddress:
        """Parse a single email address.
        Args:
            address_str: The email address to parse
        Returns:
            EmailAddress object
        """
        if not address_str:
            return EmailAddress("")

        decoded = self._decode_header(address_str)

        # Simple parsing - could be improved with proper email parsing library
        if "<" in decoded and ">" in decoded:
            name_part = decoded.split("<")[0].strip()
            email_part = decoded.split("<")[1].split(">")[0].strip()
            return EmailAddress(email_part, name_part if name_part else None)
        else:
            return EmailAddress(decoded.strip())

    def _parse_address_list(self, address_list: str) -> List[EmailAddress]:
        """Parse a list of email addresses.
        Args:
            address_list: The list of email addresses to parse
        Returns:
            List of EmailAddress objects
        """
        if not address_list:
            return []

        addresses = []
        for addr in address_list.split(","):
            addr = addr.strip()
            if addr:
                addresses.append(self._parse_address(addr))

        return addresses

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse email date string.
        Args:
            date_str: The email date string to parse
        Returns:
            datetime object if the date was parsed successfully, None otherwise
        """
        if not date_str:
            return None

        try:
            # Try parsing with email.utils.parsedate_to_datetime
            return email.utils.parsedate_to_datetime(date_str)
        except Exception:
            return None

    def _extract_body(
        self, email_msg: email.message.Message
    ) -> tuple[Optional[str], Optional[str]]:
        """Extract text and HTML body from email message.
        Args:
            email_msg: The email.message.Message object to extract the body from
        Returns:
            Tuple of text and HTML body
        """
        body_text = None
        body_html = None

        if email_msg.is_multipart():
            for part in email_msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                # Skip attachments
                if "attachment" in content_disposition:
                    continue

                if content_type == "text/plain" and not body_text:
                    body_text = part.get_payload(decode=True).decode(
                        "utf-8", errors="ignore"
                    )
                elif content_type == "text/html" and not body_html:
                    body_html = part.get_payload(decode=True).decode(
                        "utf-8", errors="ignore"
                    )
        else:
            content_type = email_msg.get_content_type()
            payload = email_msg.get_payload(decode=True)

            if payload:
                decoded_payload = payload.decode("utf-8", errors="ignore")
                if content_type == "text/plain":
                    body_text = decoded_payload
                elif content_type == "text/html":
                    body_html = decoded_payload

        return body_text, body_html

    def _extract_attachments(
        self, email_msg: email.message.Message
    ) -> List[EmailAttachment]:
        """Extract attachments from email message."""
        attachments = []

        if email_msg.is_multipart():
            for part in email_msg.walk():
                content_disposition = str(part.get("Content-Disposition"))

                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        filename = self._decode_header(filename)

                        content_type = part.get_content_type()
                        content = part.get_payload(decode=True)

                        attachments.append(
                            EmailAttachment(
                                filename=filename,
                                content_type=content_type,
                                size=len(content) if content else 0,
                                content=content,
                                content_id=part.get("Content-ID"),
                            )
                        )

        return attachments

    def _create_draft_message(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]],
        bcc: Optional[List[str]],
        attachments: Optional[List[str]],
        draft_id: str,
    ) -> str:
        """Create a properly formatted draft message for IMAP APPEND.
        Args:
            to: List of recipient email addresses
            subject: Email subject line
            body: Email body content (HTML or plain text)
            cc: Optional list of CC recipient email addresses
            bcc: Optional list of BCC recipient email addresses
            attachments: Optional list of attachment file paths
        Returns:
            String representation of the draft message
        """
        # Create the message structure
        msg = MIMEMultipart()

        # Set headers
        msg["From"] = self.credentials.username
        msg["To"] = ", ".join(to)
        msg["Subject"] = subject
        msg["Message-ID"] = f"<{draft_id}@draft>"
        msg["Date"] = email.utils.formatdate(localtime=True)

        if cc:
            msg["Cc"] = ", ".join(cc)
        if bcc:
            msg["Bcc"] = ", ".join(bcc)

        # Add body
        msg.attach(MIMEText(body, "plain"))

        # Add attachments
        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    with open(file_path, "rb") as attachment:
                        part = MIMEApplication(
                            attachment.read(), Name=Path(file_path).name
                        )
                        part["Content-Disposition"] = (
                            f'attachment; filename="{Path(file_path).name}"'
                        )
                        msg.attach(part)

        return msg.as_string()

    def _create_local_draft(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]],
        bcc: Optional[List[str]],
        attachments: Optional[List[str]],
    ) -> EmailDraft:
        """Create a local draft without storing on server.
        Args:
            to: List of recipient email addresses
            subject: Email subject line
            body: Email body content (HTML or plain text)
            cc: Optional list of CC recipient email addresses
            bcc: Optional list of BCC recipient email addresses
            attachments: Optional list of attachment file paths
        Returns:
            EmailDraft object
        """
        draft_id = f"draft_{datetime.now().timestamp()}"

        # Parse recipients
        to_addresses = [EmailAddress(addr) for addr in to]
        cc_addresses = [EmailAddress(addr) for addr in (cc or [])]
        bcc_addresses = [EmailAddress(addr) for addr in (bcc or [])]

        # Process attachments
        email_attachments = []
        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        content = f.read()

                    email_attachments.append(
                        EmailAttachment(
                            filename=Path(file_path).name,
                            content_type="application/octet-stream",
                            size=len(content),
                            content=content,
                        )
                    )

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
        )

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
        """Create and store a draft message on the server using IMAP APPEND.
        Args:
            to: List of recipient email addresses
            subject: Email subject line
            body: Email body content (HTML or plain text)
            cc: Optional list of CC recipient email addresses
            bcc: Optional list of BCC recipient email addresses
            attachments: Optional list of attachment file paths
        Returns:
            EmailDraft object
        """
        # If not connected, create a local draft only
        if not self.is_connected:
            return self._create_local_draft(to, subject, body, cc, bcc, attachments)

        draft_id = f"draft_{datetime.now().timestamp()}"

        # Parse recipients
        to_addresses = [EmailAddress(addr) for addr in to]
        cc_addresses = [EmailAddress(addr) for addr in (cc or [])]
        bcc_addresses = [EmailAddress(addr) for addr in (bcc or [])]

        # Process attachments
        email_attachments = []
        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        content = f.read()

                    email_attachments.append(
                        EmailAttachment(
                            filename=Path(file_path).name,
                            content_type="application/octet-stream",
                            size=len(content),
                            content=content,
                        )
                    )

        # Create the draft message
        draft_msg = self._create_draft_message(
            to, subject, body, cc, bcc, attachments, draft_id
        )

        try:
            # Select the drafts folder
            self._imap_client.select(folder)

            # Append the draft message to the server
            status, response = self._imap_client.append(
                folder,
                "(\\Draft)",  # Set the \Draft flag
                None,  # Use current date/time
                draft_msg.encode("utf-8"),
            )

            if status != "OK":
                raise RuntimeError(f"Failed to store draft on server: {response}")

        except Exception as e:
            raise RuntimeError(f"Failed to create draft: {str(e)}")

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
        )

    def send_message(self, draft_id: str, folder: str = "Drafts") -> bool:
        """Send a draft message by fetching from server and sending via SMTP.
        Args:
            draft_id: The ID of the draft message to send
            folder: The folder to search for the draft message
        Returns:
            True if the draft message was sent successfully, False otherwise
        """

        if not self.is_connected:
            raise ConnectionError("Not connected to email servers")
        # If draft_id starts with "draft_" and contains timestamp,
        # it's a local draft. In this case, we can't send it since
        # it wasn't stored on the server
        if draft_id.startswith("draft_") and "." in draft_id:
            raise RuntimeError(
                "Cannot send local draft - draft must be stored on server first"
            )

        try:
            # Select the drafts folder
            self._imap_client.select(folder)

            # Search for the draft message
            status, messages = self._imap_client.search(
                None, f'HEADER Message-ID "<{draft_id}@draft>"'
            )
            if status != "OK" or not messages[0]:
                raise RuntimeError(f"Draft with ID {draft_id} not found")

            msg_ids = messages[0].split()
            if not msg_ids:
                raise RuntimeError(f"Draft with ID {draft_id} not found")

            # Fetch the draft message
            status, msg_data = self._imap_client.fetch(msg_ids[0], "(RFC822)")
            if status != "OK":
                raise RuntimeError("Failed to fetch draft message")

            # Send the message via SMTP
            raw_email = msg_data[0][1]
            self._smtp_client.send_message(email.message_from_bytes(raw_email))

            # Optionally delete the draft after sending
            # self._imap_client.store(msg_ids[0], "+FLAGS", "\\Deleted")

            return True
        except Exception as e:
            raise RuntimeError(f"Failed to send draft message: {str(e)}")

    def send_message_direct(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
    ) -> bool:
        """Send a message directly via SMTP.
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
        if not self.is_connected or not self._smtp_client:
            raise ConnectionError("Not connected to SMTP server")

        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.credentials.username
            msg["To"] = ", ".join(to)
            msg["Subject"] = subject

            if cc:
                msg["Cc"] = ", ".join(cc)
            if bcc:
                msg["Bcc"] = ", ".join(bcc)

            # Add body
            msg.attach(MIMEText(body, "plain"))

            # Add attachments
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as attachment:
                            part = MIMEApplication(
                                attachment.read(), Name=Path(file_path).name
                            )
                            part["Content-Disposition"] = (
                                f'attachment; filename="{Path(file_path).name}"'
                            )
                            msg.attach(part)

            # Send message
            all_recipients = to + (cc or []) + (bcc or [])
            self._smtp_client.send_message(msg, to_addrs=all_recipients)

            return True

        except Exception as e:
            raise RuntimeError(f"Failed to send message: {str(e)}")

    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read.
        Args:
            message_id: The ID of the message to mark as read
        Returns:
            True if the message was marked as read successfully, False otherwise
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to IMAP server")

        try:
            # Search for the message
            status, messages = self._imap_client.search(
                None, f'HEADER Message-ID "{message_id}"'
            )
            if status != "OK" or not messages[0]:
                return False

            msg_ids = messages[0].split()
            if not msg_ids:
                return False

            # Mark as read
            self._imap_client.store(msg_ids[0], "+FLAGS", "\\Seen")
            return True

        except Exception:
            return False

    def get_folders(self) -> List[str]:
        """Get list of available folders.
        Returns:
            List of available folders
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to IMAP server")

        try:
            status, folders = self._imap_client.list()
            if status != "OK":
                return []

            folder_list = []
            for folder in folders:
                folder_str = folder.decode()
                # Extract folder name from IMAP response
                folder_name = folder_str.split(' "/" ')[-1].strip('"')
                folder_list.append(folder_name)

            return folder_list

        except Exception:
            return []

    @property
    def is_connected(self) -> bool:
        """Check if connected to email servers.
        Returns:
            True if connected to email servers, False otherwise
        """
        return (
            self._connected
            and self._imap_client is not None
            and self._smtp_client is not None
        )
