# Contacts App Integration

## Overview

The Contacts integration provides access to the macOS Contacts application, allowing you to search for contacts by name or phone number.

## Endpoints

| Endpoint                   | File                 | Description                      |
| -------------------------- | -------------------- | -------------------------------- |
| `contacts_search_by_name`  | `search_by_name.py`  | Search contacts by name          |
| `contacts_search_by_phone` | `search_by_phone.py` | Look up contacts by phone number |

## Key Features

- Fuzzy name matching for better search results
- Phone number normalization for consistent lookups
- Structured contact data including phones, emails, and addresses
- Support for both partial and exact phone number matching

## Usage Examples

### Search by Name

```python
from apps.contacts.search_by_name import search_by_name_logic

result = search_by_name_logic("John")
if result["success"]:
    for contact in result["contacts"]:
        print(f"{contact['display_name']}")
        if contact.get("phones"):
            for phone in contact["phones"]:
                print(f"  {phone['label']}: {phone['number']}")
```

### Search by Phone Number

```python
from apps.contacts.search_by_phone import search_by_phone_logic

# Partial matching
result = search_by_phone_logic("1234")

# Exact matching
exact_result = search_by_phone_logic("+1-800-123-4567", exact_match=True)
```

## Response Format

```json
{
  "success": true,
  "contacts": [
    {
      "id": "AB1234567",
      "display_name": "Jane Smith",
      "first_name": "Jane",
      "last_name": "Smith",
      "phones": [
        {
          "label": "mobile",
          "number": "+1 (555) 123-4567"
        }
      ],
      "emails": [
        {
          "label": "work",
          "address": "jane.smith@example.com"
        }
      ],
      "addresses": [
        {
          "label": "home",
          "formatted_address": "123 Main St, Anytown, CA 94043, USA"
        }
      ],
      "organization": "Acme Corporation",
      "job_title": "Senior Developer"
    }
  ],
  "total_found": 1,
  "message": "Found 1 contact matching 'Jane'"
}
```

## Implementation Notes

- Uses AppleScript to interact with the Contacts app
- Handles parameter embedding directly in AppleScript
- Uses custom delimiters for structured data return
- Provides proper phone number normalization for matching
