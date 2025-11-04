"""Example usage of the email utilities.

This file is used to test the email utilities.

To run the examples, you need to have a Gmail account with 2-factor authentication enabled.
You need to generate an app password for the account.

Environment Variables (.env file):
- EMAIL: Your Gmail address
- PASSWORD: Your Gmail app password
- RECIPIENT: Email address for test messages
- WEAVIATE_URL: Weaviate server URL (defaults to http://localhost:8080)

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
import os
from typing import List

from dotenv import load_dotenv

from ragora.core import EmailPreprocessor
from ragora.utils import (
    EmailProvider,
    EmailProviderFactory,
    GraphCredentials,
    IMAPCredentials,
    ProviderType,
)


def get_user_credentials_from_file():
    """Get email credentials from a .env file."""
    # load the .env file
    load_dotenv()
    # get the email, password and recipient from the .env file
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")
    recipient = os.getenv("RECIPIENT")
    return email, password, recipient


def get_weaviate_url_from_file():
    """Get Weaviate URL from a .env file."""
    # load the .env file
    load_dotenv()
    # get the weaviate_url from the .env file
    weaviate_url = os.getenv("WEAVIATE_URL")
    return weaviate_url


def get_user_credentials():
    """Get email credentials from user input."""
    print("=== Email Credentials Setup ===")
    # if credentials are provided in the .env file, use them
    email, password, recipient = get_user_credentials_from_file()
    if email and password and recipient:
        return email, password, recipient

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
        messages = provider.fetch_messages(limit=10, unread_only=False)
        print(f"Fetched {len(messages)} latest messages")

        # Process messages
        for msg in messages:
            print(f"Subject: {msg.subject}")
            print(f"From: {msg.sender}")
            print(f"Date: {msg.date_sent}")
            print(f"Body preview: {msg.get_body()[:100]}...")
            print(f"Cleaned body: {EmailPreprocessor().clean_email_body(msg)}")
            print("-" * 50)

        # getting the list of folders
        folders = provider.get_folders()
        print(f"Available folders: {folders}")

        # Create and send a draft
        draft = provider.create_draft(
            to=[recipient],
            subject="Test Email from RAG System",
            body="This is a test email sent from the RAG system.",
            cc=["cc@example.com"],
            folder="[Gmail]/Drafts",
        )
        print(f"Created draft with ID: {draft.draft_id}")

        # Send message directly
        success = provider.send_message_direct(
            to=[recipient],
            subject="Direct Email from RAG System",
            body="This email was sent directly without creating a draft.",
        )
        print(f"Message sent successfully: {success}")

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


def example_email_database_creation():
    """Example of creating an email knowledge base using KnowledgeBaseManager."""
    print("=== Email Database Creation Example ===")

    from ragora import KnowledgeBaseManager, SearchStrategy

    # Get credentials
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
        smtp_port=465,
        username=email,
        password=password,
        use_ssl=True,
        use_tls=False,
    )

    # Create provider
    provider = EmailProviderFactory.create_provider(ProviderType.IMAP, credentials)

    # Get Weaviate URL from .env file or use default
    weaviate_url = get_weaviate_url_from_file() or "http://localhost:8080"

    # Initialize Knowledge Base Manager
    kbm = KnowledgeBaseManager(weaviate_url=weaviate_url)

    try:
        # Connect to email servers
        provider.connect()
        print("Connected to email servers")

        # Process emails from inbox and store in knowledge base
        print("\nProcessing emails from INBOX...")
        print(
            "Note: Email chunks will include full metadata (subject, sender, recipient, etc.)"
        )
        print(
            "      and support custom metadata for enhanced filtering and organization."
        )
        stored_ids = kbm.process_email_account(
            email_provider=provider, folder="INBOX", collection="Email"
        )
        print(f"Stored {len(stored_ids)} email chunks in knowledge base")

        # Search for emails
        print("\nSearching for emails about 'meeting'...")
        results = kbm.search("meeting", collection="Email", top_k=3)
        print(f"Found {results.total_found} relevant emails")

        for i, result in enumerate(results.results, 1):
            print(f"\n{i}. {result.subject or 'No subject'}")
            print(f"   Sender: {result.sender or 'Unknown'}")
            print(f"   Content preview: {result.content[:100]}...")
            print(f"   Similarity score: {result.similarity_score:.3f}")

        new_emails_info = kbm.check_new_emails(
            email_provider=provider,
            folder="INBOX",
            include_body=True,
            limit=5,
        )

        if new_emails_info["count"] > 0:
            # Process unread emails only
            print("\n\nProcessing new unread emails...")
            new_stored = kbm.process_new_emails(
                email_provider=provider,
                email_ids=[
                    email["email_id"] for email in new_emails_info["emails"][:3]
                ],
                collection="Email",
            )
            print(f"Stored {len(new_stored)} new email chunks")
        else:
            print("No new emails found")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        provider.disconnect()
        print("\nDisconnected from email servers")


def example_email_answer_drafting_workflow():
    """Example workflow for LLM-based answer drafting using email knowledge base."""
    print("=== Email Answer Drafting Workflow Example ===")

    from ragora import KnowledgeBaseManager, SearchStrategy

    # Get credentials
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
        smtp_port=465,
        username=email,
        password=password,
        use_ssl=True,
        use_tls=False,
    )

    # Create provider
    provider = EmailProviderFactory.create_provider(ProviderType.IMAP, credentials)

    # Get Weaviate URL from .env file or use default
    weaviate_url = get_weaviate_url_from_file() or "http://localhost:8080"

    # Initialize Knowledge Base Manager
    kbm = KnowledgeBaseManager(weaviate_url=weaviate_url)

    try:
        # Step 1: Check for new emails (read-only, includes body for LLM)
        print("\nStep 1: Checking for new emails...")
        new_emails_info = kbm.check_new_emails(
            email_provider=provider, folder="INBOX", include_body=True, limit=5
        )
        print(f"Found {new_emails_info['count']} new emails")

        # Step 2: For each email, find relevant context from knowledge base
        print("\nStep 2: Finding relevant context for drafting replies...")
        for email_data in new_emails_info["emails"][:3]:  # Process first 3
            print(f"\n--- Processing: {email_data['subject']} ---")
            print(f"From: {email_data['sender']}")

            # Search for relevant context in knowledge base
            query = email_data["subject"] + " " + email_data.get("body", "")[:100]
            context_results = kbm.search(query=query, collection="Email", top_k=2)

            print(f"Found {context_results.total_found} relevant context items")
            for i, context in enumerate(context_results.results, 1):
                print(f"  {i}. {context.subject or 'No subject'}")

            # In a real scenario, this would be passed to an LLM
            print("  → LLM would draft reply using this context")
            print("  → Draft would be created using EmailProvider")
            print("  → User would review and send")

        # Step 3: After handling emails, index them in knowledge base
        print("\n\nStep 3: Indexing processed emails...")
        # Extract email IDs from the emails we processed
        processed_email_ids = [
            email["email_id"] for email in new_emails_info["emails"][:3]
        ]
        stored_ids = kbm.process_new_emails(
            email_provider=provider, email_ids=processed_email_ids, collection="Email"
        )
        print(f"Indexed {len(stored_ids)} email chunks")

        print("\nWorkflow complete!")
        print(
            "Note: Actual LLM integration and email sending would happen in your application"
        )

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


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
        """Note: before running the examples, you need to create a .env file with the following variables:
- EMAIL: Your Gmail address
- PASSWORD: Your Gmail app password
- RECIPIENT: Email address for test messages
- WEAVIATE_URL: Weaviate server URL (defaults to http://localhost:8080)
"""
    )
    print()

    # Run the interactive examples
    # example_imap_usage()
    # example_graph_usage()
    example_email_database_creation()
    # example_email_answer_drafting_workflow()

    print("Note: Uncomment desired examples in main() to run them")


if __name__ == "__main__":
    main()
