# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python library for interacting with the Gmail API. It provides a simple wrapper around Google's official Gmail API client for reading, sending, and managing emails.

## Development Commands

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Example
```bash
python example_usage.py
```

### Use the Library
```python
from gmail_client import get_service, list_messages, get_message

service = get_service()  # Authenticates and returns Gmail API service
messages = list_messages(service, query='is:unread', max_results=10)
```

## Architecture

### Core Files

- **gmail_client.py** - Main module containing all Gmail API functions
- **example_usage.py** - Demonstrates how to use the library
- **requirements.txt** - Python dependencies (google-api-python-client, google-auth)

### Authentication Flow

The library uses OAuth 2.0 for authentication:

1. **First run**: Requires `credentials.json` from Google Cloud Console
   - Download from: Google Cloud Console > APIs & Services > Credentials > OAuth client ID (Desktop app)
   - Enable Gmail API in the project

2. **Token persistence**: After first authentication, `token.json` is created for subsequent runs

3. **Token refresh**: Automatic when token expires (uses refresh_token)

### API Functions

All functions in `gmail_client.py` accept a `service` object (returned by `get_service()`):

| Function | Purpose |
|----------|---------|
| `get_service()` | Authenticate and return Gmail API service object |
| `list_messages(service, query, max_results)` | Search emails using Gmail query syntax |
| `get_message(service, msg_id)` | Fetch full email details by ID |
| `send_message(service, to, subject, body, attachments)` | Send email (HTML or plain text) |
| `mark_as_read(service, msg_id)` | Remove UNREAD label |
| `trash_message(service, msg_id)` | Move to trash |
| `get_unread_count(service)` | Get unread inbox count |

### Gmail Query Syntax

The `list_messages()` function accepts standard Gmail search queries:
- `is:unread` - Unread emails
- `from:email@example.com` - From specific sender
- `subject:meeting` - Subject contains text
- `after:2024/01/01` - After date
- `has:attachment` - Has attachments
- `in:spam` - In spam folder

### Security Notes

- `credentials.json` and `token.json` are git-ignored files containing OAuth secrets
- `credentials.json` is downloaded from Google Cloud Console once
- `token.json` is auto-generated on first authentication
- Both files should never be committed to version control
