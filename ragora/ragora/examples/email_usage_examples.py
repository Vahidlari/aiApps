"""Example usage of the email utilities.

This file is used to test the email utilities.

To run the examples, you need to have a Gmail account with 2-factor authentication enabled.
You need to generate an app password for the account.

Run the example with:
python -m ragora.examples.email_usage_examples

Hints:

# Gmail App Password Setup Guide

## Step-by-Step Instructions to Find App Passwords

### Method 1: Direct Link (Easiest)
1. Go directly to: https://myaccount.google.com/apppasswords
2. You'll be prompted to sign in to your Google account
3. Select "Mail" from the dropdown
4. Click "Generate"
5. Copy the 16-character password (it looks like: `abcd efgh ijkl mnop`)

### Method 2: Through Google Account Settings
1. Go to [Google Account](https://myaccount.google.com/)
2. Click on **Security** (left sidebar)
3. Under "Signing in to Google":
   - Make sure **2-Step Verification** is turned ON
   - If not, enable it first (this is required for App Passwords)
4. Look for **App passwords** (should be right below 2-Step Verification)
5. Click **App passwords**
6. Select **Mail** from the dropdown
7. Click **Generate**
8. Copy the password

### Method 3: If You Can't Find App Passwords
**This usually means 2-Step Verification is not enabled:**

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Find **2-Step Verification** and turn it ON
3. Follow the setup process (you'll need your phone)
4. Once enabled, **App passwords** will appear below it
5. Now follow Method 2 above

### Method 4: Organization/Work Accounts
If you're using a work/school Gmail account:
- App passwords might be disabled by your organization
- Contact your IT administrator
- You may need to use OAuth2 instead (Microsoft Graph API)

## Important Notes

### ✅ Requirements for App Passwords:
- **2-Factor Authentication MUST be enabled**
- **Personal Google account** (not organization-managed)
- **Recent Google account** (some very old accounts may not have this option)

### ❌ Common Issues:
- **Can't find App passwords**: 2FA not enabled
- **Option grayed out**: Organization account restrictions
- **"Not available"**: Account doesn't meet requirements

### 🔧 Alternative Solutions:

#### Option 1: Use Microsoft Graph API Instead
If you have a Microsoft 365 account, we can switch to Graph API which uses OAuth2.

#### Option 2: Use OAuth2 for Gmail
We can modify the code to use OAuth2 authentication instead of App passwords.

#### Option 3: Test with Different Account
Try with a personal Gmail account if you're using a work account.

## What the App Password Looks Like
- **Format**: 16 characters with spaces: `abcd efgh ijkl mnop`
- **Usage**: Remove spaces when using in code: `abcdefghijklmnop`
- **Security**: This is NOT your regular Gmail password

## Still Having Issues?

1. **Check 2FA Status**: Go to https://myaccount.google.com/security
2. **Try Incognito Mode**: Sometimes browser extensions interfere
3. **Contact Support**: If using personal account and still can't find it
4. **Alternative Authentication**: We can implement OAuth2 flow
"""

import getpass
from typing import List

from ragora.utils import (
    EmailProvider,
    EmailProviderFactory,
    GraphCredentials,
    IMAPCredentials,
    ProviderType,
)


def get_user_credentials():
    """Get email credentials from user input."""
    print("=== Email Credentials Setup ===")

    # Get Gmail address
    email = input("Enter your Gmail address: ").strip()
    if not email.endswith("@gmail.com"):
        print(
            "Warning: This example is configured for Gmail. Other providers may need different settings."
        )

    # Get password (hidden input)
    password = getpass.getpass("Enter your Gmail app password: ")
    print("password: ", password)

    # Get recipient email
    recipient = input("Enter recipient email address: ").strip()

    return email, password, recipient


def example_imap_usage():
    """Example of using IMAP provider with user input."""
    print("=== IMAP Provider Example ===")

    # Get credentials from user
    try:
        email, password, recipient = get_user_credentials()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return
    except Exception as e:
        print(f"Error getting credentials: {e}")
        return

    # Create IMAP credentials
    credentials = IMAPCredentials(
        imap_server="imap.gmail.com",
        imap_port=993,
        smtp_server="smtp.gmail.com",
        smtp_port=465,  # Gmail SMTP SSL port
        username=email,
        password=password,  # Use app password for Gmail
        use_ssl=True,
        use_tls=False,  # Use SSL instead of TLS for SMTP
    )

    # Create provider
    provider = EmailProviderFactory.create_provider(ProviderType.IMAP, credentials)

    try:
        # Connect to email servers
        provider.connect()
        print("Connected to IMAP/SMTP servers")

        # Fetch messages
        messages = provider.fetch_messages(limit=10, unread_only=True)
        print(f"Fetched {len(messages)} unread messages")

        # Process messages
        for msg in messages:
            print(f"Subject: {msg.subject}")
            print(f"From: {msg.sender}")
            print(f"Date: {msg.date_sent}")
            print(f"Body preview: {msg.get_body()[:100]}...")
            print("-" * 50)

        # Create and send a draft
        draft = provider.create_draft(
            to=[recipient],
            subject="Test Email from RAG System",
            body="This is a test email sent from the RAG system.",
            cc=["cc@example.com"],
        )
        print(f"Created draft with ID: {draft.draft_id}")

        # Send message directly
        success = provider.send_message_direct(
            to=[recipient],
            subject="Direct Email from RAG System",
            body="This email was sent directly without creating a draft.",
        )
        print(f"Message sent successfully: {success}")

        # Get available folders
        folders = provider.get_folders()
        print(f"Available folders: {folders}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        provider.disconnect()
        print("Disconnected from email servers")


def example_graph_usage():
    """Example of using Microsoft Graph provider."""
    print("=== Microsoft Graph Provider Example ===")

    # Create Graph credentials
    credentials = GraphCredentials(
        client_id="your-client-id",
        client_secret="your-client-secret",
        tenant_id="your-tenant-id",
        access_token="your-access-token",  # Optional if using client credentials
    )

    # Create provider
    provider = EmailProviderFactory.create_provider(ProviderType.GRAPH, credentials)

    try:
        # Connect to Graph API
        provider.connect()
        print("Connected to Microsoft Graph API")

        # Fetch messages
        messages = provider.fetch_messages(limit=10, folder="inbox")
        print(f"Fetched {len(messages)} messages from inbox")

        # Process messages
        for msg in messages:
            print(f"Subject: {msg.subject}")
            print(f"From: {msg.sender}")
            print(f"Status: {msg.status.value}")
            print(f"Has attachments: {len(msg.attachments) > 0}")
            print("-" * 50)

        # Create a draft
        draft = provider.create_draft(
            to=["colleague@company.com"],
            subject="Meeting Notes from RAG System",
            body="<h1>Meeting Notes</h1><p>Here are the key points from our meeting...</p>",
            cc=["manager@company.com"],
        )
        print(f"Created draft with ID: {draft.draft_id}")

        # Send the draft
        success = provider.send_message(draft.draft_id)
        print(f"Draft sent successfully: {success}")

        # Mark a message as read
        if messages:
            first_msg = messages[0]
            read_success = provider.mark_as_read(first_msg.message_id)
            print(f"Marked message as read: {read_success}")

        # Get available folders
        folders = provider.get_folders()
        print(f"Available folders: {folders}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        provider.disconnect()
        print("Disconnected from Microsoft Graph API")


def example_rag_integration():
    """Example of integrating email utilities with RAG system."""
    print("=== RAG Integration Example ===")

    # This would typically be used within a RAG system
    def create_email_database(provider: EmailProvider, limit: int = 100) -> List[dict]:
        """Create a database of emails for RAG system."""
        try:
            provider.connect()

            # Fetch messages
            messages = provider.fetch_messages(limit=limit)

            # Convert to database format
            email_database = []
            for msg in messages:
                email_data = {
                    "message_id": msg.message_id,
                    "subject": msg.subject,
                    "sender": str(msg.sender),
                    "recipients": [str(addr) for addr in msg.recipients],
                    "body": msg.get_body(),
                    "date_sent": msg.date_sent.isoformat() if msg.date_sent else None,
                    "date_received": (
                        msg.date_received.isoformat() if msg.date_received else None
                    ),
                    "status": msg.status.value,
                    "attachments": [att.filename for att in msg.attachments],
                    "folder": msg.folder,
                }
                email_database.append(email_data)

            return email_database

        except Exception as e:
            print(f"Error creating email database: {e}")
            return []
        finally:
            provider.disconnect()

    def generate_email_reply(
        provider: EmailProvider, message_id: str, rag_response: str
    ) -> bool:
        """Generate and send an email reply using RAG system response."""
        try:
            provider.connect()

            # Fetch the original message
            original_msg = provider.fetch_message_by_id(message_id)
            if not original_msg:
                print(f"Message {message_id} not found")
                return False

            # Create reply subject
            reply_subject = f"Re: {original_msg.subject}"
            if not reply_subject.startswith("Re: "):
                reply_subject = f"Re: {reply_subject}"

            # Create reply body
            reply_body = f"""
Hi {original_msg.sender.name or original_msg.sender.email},

{rag_response}

Best regards,
RAG Assistant
            """.strip()

            # Send reply
            success = provider.send_message_direct(
                to=[original_msg.sender.email], subject=reply_subject, body=reply_body
            )

            return success

        except Exception as e:
            print(f"Error generating reply: {e}")
            return False
        finally:
            provider.disconnect()

    # Example usage with IMAP
    print("Creating email database with IMAP provider...")
    imap_credentials = IMAPCredentials(
        imap_server="imap.gmail.com",
        imap_port=993,
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        username="your-email@gmail.com",
        password="your-app-password",
    )

    imap_provider = EmailProviderFactory.create_provider(
        ProviderType.IMAP, imap_credentials
    )
    email_db = create_email_database(imap_provider, limit=10)
    print(f"Created database with {len(email_db)} emails")

    # Example of generating a reply (would use actual RAG response)
    if email_db:
        sample_msg_id = email_db[0]["message_id"]
        rag_response = "Based on the email content, here is my response..."
        reply_sent = generate_email_reply(imap_provider, sample_msg_id, rag_response)
        print(f"Reply sent: {reply_sent}")


def main():
    """Run all examples."""
    print("Email Utilities Examples")
    print("=" * 50)
    print()
    print("IMPORTANT: Gmail Setup Instructions")
    print("-" * 40)
    print("1. Enable 2-Factor Authentication on your Gmail account")
    print("2. Generate an App Password:")
    print("   - Go to Google Account settings")
    print("   - Security > 2-Step Verification > App passwords")
    print("   - Generate password for 'Mail'")
    print("3. Use the generated app password (not your regular Gmail password)")
    print()
    print("Gmail Server Settings:")
    print("- IMAP: imap.gmail.com:993 (SSL)")
    print("- SMTP: smtp.gmail.com:465 (SSL)")
    print()
    print(
        "Note: You'll be prompted to enter your credentials when running the example."
    )
    print()

    # Run the interactive example
    example_imap_usage()
    # example_graph_usage()
    # example_rag_integration()


if __name__ == "__main__":
    main()
