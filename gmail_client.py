"""
Gmail API Client for reading and sending emails.

Setup:
1. Go to https://console.cloud.google.com/
2. Create a new project or select existing one
3. Enable the Gmail API: APIs & Services > Enable APIs and Services > Search "Gmail API" > Enable
4. Create OAuth credentials: APIs & Services > Credentials > Create Credentials > OAuth client ID
   - Application type: Desktop app
   - Name: Gmail Client
5. Download the client configuration and save as 'credentials.json' in this directory
6. Run this script - it will open a browser for authentication on first run

The token will be saved as 'token.json' for future runs.
"""

import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete token.json to re-authenticate
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]


def get_service():
    """Authenticate and return Gmail API service."""
    creds = None
    token_path = 'token.json'
    credentials_path = 'credentials.json'

    # Load existing token
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(
                    f"'{credentials_path}' not found. "
                    "Please download it from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save token for future runs
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)


def list_messages(service, query='', max_results=10):
    """
    List emails matching a query.

    Args:
        service: Gmail API service
        query: Gmail search query (e.g., 'from:someone@gmail.com', 'is:unread', 'after:2024/01/01')
        max_results: Maximum number of results to return

    Returns:
        List of message dictionaries with 'id' and 'threadId'
    """
    try:
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()
        messages = results.get('messages', [])
        return messages
    except HttpError as error:
        print(f'An error occurred: {error}')
        return []


def get_message(service, msg_id):
    """
    Get full message details by ID.

    Returns:
        Dictionary with: id, threadId, subject, sender, date, body, snippet
    """
    try:
        message = service.users().messages().get(
            userId='me',
            id=msg_id,
            format='full'
        ).execute()

        # Extract headers
        headers = message['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
        date = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'Unknown')

        # Extract body
        body = get_message_body(message['payload'])

        return {
            'id': msg_id,
            'threadId': message['threadId'],
            'subject': subject,
            'sender': sender,
            'date': date,
            'snippet': message.get('snippet', ''),
            'body': body,
            'labels': message.get('labelIds', [])
        }
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None


def get_message_body(payload):
    """Extract text body from message payload."""
    body = ''

    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
            elif part['mimeType'] == 'text/html':
                data = part['body'].get('data', '')
                if data and not body:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
    else:
        data = payload['body'].get('data', '')
        if data:
            body = base64.urlsafe_b64decode(data).decode('utf-8')

    return body


def send_message(service, to, subject, body, attachments=None):
    """
    Send an email.

    Args:
        service: Gmail API service
        to: Recipient email address
        subject: Email subject
        body: Email body (HTML or plain text)
        attachments: Optional list of file paths to attach
    """
    try:
        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject

        # Add body
        msg_body = MIMEText(body, 'html' if '<' in body else 'plain')
        message.attach(msg_body)

        # Add attachments
        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    part = MIMEBase('application', 'octet-stream')
                    with open(file_path, 'rb') as f:
                        part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(file_path)}'
                    )
                    message.attach(part)

        # Encode and send
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        send_message = {'raw': raw}

        sent = service.users().messages().send(userId='me', body=send_message).execute()
        print(f"Message sent! ID: {sent['id']}")
        return sent['id']

    except HttpError as error:
        print(f'An error occurred: {error}')
        return None


def mark_as_read(service, msg_id):
    """Mark a message as read."""
    try:
        service.users().messages().modify(
            userId='me',
            id=msg_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        print(f"Message {msg_id} marked as read")
    except HttpError as error:
        print(f'An error occurred: {error}')


def trash_message(service, msg_id):
    """Move a message to trash."""
    try:
        service.users().messages().trash(userId='me', id=msg_id).execute()
        print(f"Message {msg_id} moved to trash")
    except HttpError as error:
        print(f'An error occurred: {error}')


def get_unread_count(service):
    """Get count of unread messages in inbox."""
    try:
        results = service.users().labels().get(userId='me', id='INBOX').execute()
        return results.get('messagesUnread', 0)
    except HttpError as error:
        print(f'An error occurred: {error}')
        return 0


if __name__ == '__main__':
    # Example usage
    print("Gmail API Client")
    print("=" * 50)
    print("\n1. Make sure you have 'credentials.json' from Google Cloud Console")
    print("2. Run the functions to authenticate and access your Gmail")
    print("\nExample:")
    print("  service = get_service()")
    print("  messages = list_messages(service, query='is:unread', max_results=5)")
    print("  for msg in messages:")
    print("      details = get_message(service, msg['id'])")
    print("      print(details['subject'])")
