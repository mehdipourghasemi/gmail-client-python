"""
Example: Check unread emails and send a test email.
"""
from gmail_client import get_service, list_messages, get_message, send_message, get_unread_count

# Authenticate (opens browser on first run)
service = get_service()

# Check unread count
unread = get_unread_count(service)
print(f"You have {unread} unread messages\n")

# List recent unread emails
print("Recent unread emails:")
print("-" * 50)
messages = list_messages(service, query='is:unread', max_results=5)

for msg in messages:
    details = get_message(service, msg['id'])
    print(f"From: {details['sender']}")
    print(f"Subject: {details['subject']}")
    print(f"Date: {details['date']}")
    print(f"Snippet: {details['snippet'][:100]}...")
    print("-" * 50)

# Example: Send an email (uncomment to use)
# send_message(
#     service,
#     to='recipient@example.com',
#     subject='Test from Python',
#     body='<h1>Hello!</h1><p>This is a test email.</p>'
# )
