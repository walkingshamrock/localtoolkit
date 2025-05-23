# Messages App Integration

## Overview

The Messages integration provides access to the macOS Messages application, allowing you to list conversations, retrieve messages, and send messages.

## Endpoints

| Endpoint                      | File                    | Description                           |
| ----------------------------- | ----------------------- | ------------------------------------- |
| `messages_list_conversations` | `list_conversations.py` | List available conversations          |
| `messages_get_messages`       | `get_messages.py`       | Retrieve messages from a conversation |
| `messages_send_message`       | `send_message.py`       | Send a message to a conversation      |

## Key Features

- **Dual Retrieval**: Uses direct SQLite access (primary) with AppleScript fallback
- **Message Type Classification**: Properly identifies message types (text, image, video, etc.)
- **URL Extraction**: Extracts URLs from link preview messages
- **Attachment Support**: Provides complete metadata for message attachments

## Usage Examples

### List Conversations

```python
from apps.messages.list_conversations import list_conversations_logic

result = list_conversations_logic()
if result["success"]:
    for conversation in result["conversations"]:
        print(f"{conversation['display_name']} - {conversation['id']}")
```

### Get Messages

```python
from apps.messages.get_messages import get_messages_logic

result = get_messages_logic(
    conversation_id="iMessage;-;+1234567890",
    limit=10,
    include_attachments=True
)

if result["success"]:
    for message in result["messages"]:
        sender = "You" if message["is_from_me"] else message["sender"]
        print(f"{sender}: {message['text']}")
```

### Send Message

```python
from apps.messages.send_message import send_message_logic

result = send_message_logic(
    conversation_id="iMessage;-;+1234567890",
    text="Hello from LocalToolKit!"
)
```

## Response Formats

### List Conversations Response

```json
{
  "success": true,
  "conversations": [
    {
      "id": "iMessage;-;+1234567890",
      "display_name": "John Smith",
      "is_group_chat": false,
      "last_message": {
        "text": "Hello",
        "date": "2023-05-30 10:23:39"
      },
      "unread_count": 0
    }
  ],
  "message": "Successfully retrieved conversations"
}
```

### Get Messages Response

```json
{
  "success": true,
  "messages": [
    {
      "id": "1234567",
      "text": "Hello",
      "date": "2023-05-30 10:23:39",
      "sender": "+1234567890",
      "is_from_me": false,
      "message_type": "text",
      "has_attachments": false
    }
  ],
  "conversation_info": {
    "id": "iMessage;-;+1234567890",
    "message_count": 1
  },
  "message": "Successfully retrieved 1 message"
}
```
