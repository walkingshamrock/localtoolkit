# Mail App Integration

## Overview

The Mail integration provides access to the macOS Mail application, allowing you to send emails and create draft messages.

## Endpoints

| Endpoint          | File            | Description                             |
| ----------------- | --------------- | --------------------------------------- |
| `mail_send_mail`  | `send_mail.py`  | Send an email with optional attachments |
| `mail_draft_mail` | `draft_mail.py` | Create a draft email                    |

## Key Features

- Multiple recipients, CC and BCC support
- File attachments using absolute file paths
- Plain text or HTML email content
- Draft creation with identifiers for reference

## Usage Examples

### Send an Email

```python
from apps.mail.send_mail import send_mail_logic

# Simple email
result = send_mail_logic(
    to=["recipient@example.com"],
    subject="Hello from LocalToolKit",
    body="This is a test email sent via LocalToolKit."
)

# With attachments and CC/BCC
result = send_mail_logic(
    to=["recipient1@example.com", "recipient2@example.com"],
    subject="Project Documents",
    body="Please find the requested documents attached.",
    cc=["manager@example.com"],
    bcc=["archive@example.com"],
    attachments=["/Users/username/Documents/report.pdf"]
)
```

### Create a Draft Email

```python
from apps.mail.draft_mail import draft_mail_logic

result = draft_mail_logic(
    to=["recipient@example.com"],
    subject="Hello from LocalToolKit!",
    body="<h1>Hello!</h1><p>This is an HTML email.</p>",
    html_body=True
)

if result["success"]:
    print(f"Draft created with ID: {result['draft_id']}")
```

## Response Format

```json
{
  "success": true,
  "message": "Email sent successfully to 2 recipients",
  "metadata": {
    "to_count": 2,
    "cc_count": 1,
    "bcc_count": 1,
    "attachment_count": 1
  }
}
```

## Requirements

- Mail app configured with at least one email account
- Proper macOS permissions for script execution
- Default account will be used as the sender
