"""
Test data generators for mac-mcp tests.

This module provides functions for generating realistic test data
for each app integration, ensuring consistent test data across tests.
"""

import random
import uuid
import datetime
from typing import List, Dict, Any, Optional


def generate_message_id() -> str:
    """
    Generate a unique message identifier.
    
    Returns:
        str: A unique message ID in the format used by Messages app
    """
    return f"p:{uuid.uuid4()}"


def generate_conversation_id() -> str:
    """
    Generate a unique conversation identifier.
    
    Returns:
        str: A unique conversation ID in the format used by Messages app
    """
    return f"iMessage;-;+{random.randint(1000000000, 9999999999)}"


def generate_timestamp(days_ago: int = 0, hours_ago: int = 0, minutes_ago: int = 0) -> float:
    """
    Generate a timestamp for a message or event.
    
    Args:
        days_ago (int, optional): Number of days in the past. Default is 0.
        hours_ago (int, optional): Number of hours in the past. Default is 0.
        minutes_ago (int, optional): Number of minutes in the past. Default is 0.
        
    Returns:
        float: Unix timestamp
    """
    delta = datetime.timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
    timestamp = datetime.datetime.now() - delta
    return timestamp.timestamp()


def generate_message(
    text: Optional[str] = None,
    is_from_me: bool = False,
    days_ago: int = 0,
    conversation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a realistic message object for testing.
    
    Args:
        text (str, optional): Message content. If None, a random message is generated.
        is_from_me (bool, optional): Whether the message is from the user. Default is False.
        days_ago (int, optional): Number of days in the past. Default is 0.
        conversation_id (str, optional): Conversation ID. If None, one will be generated.
        
    Returns:
        dict: A message object with realistic properties
    """
    if text is None:
        messages = [
            "Hello there!",
            "How are you doing?",
            "Just checking in.",
            "Did you see that email I sent?",
            "Can we meet tomorrow?",
            "I'll be running late.",
            "Thanks for your help!",
            "Let me know when you're free.",
            "Have a good day!",
            "I'll get back to you soon."
        ]
        text = random.choice(messages)
    
    if conversation_id is None:
        conversation_id = generate_conversation_id()
    
    sender_name = "Me" if is_from_me else "John Doe"
    sender_id = "me" if is_from_me else f"person:{uuid.uuid4()}"
    
    return {
        "id": generate_message_id(),
        "text": text,
        "date": generate_timestamp(days_ago=days_ago),
        "sender": {
            "name": sender_name,
            "id": sender_id
        },
        "is_from_me": is_from_me,
        "message_type": "text",
        "conversation_id": conversation_id,
        "attachments": []
    }


def generate_conversation(
    display_name: Optional[str] = None,
    is_group_chat: bool = False,
    message_count: int = 5
) -> Dict[str, Any]:
    """
    Generate a realistic conversation object for testing.
    
    Args:
        display_name (str, optional): Name of the conversation.
        is_group_chat (bool, optional): Whether it's a group chat. Default is False.
        message_count (int, optional): Number of messages to include. Default is 5.
        
    Returns:
        dict: A conversation object with realistic properties
    """
    if display_name is None:
        if is_group_chat:
            group_names = ["Family", "Work Team", "Project X", "Weekend Plans", "Old Friends"]
            display_name = random.choice(group_names)
        else:
            first_names = ["John", "Sarah", "Mike", "Emma", "David", "Lisa"]
            last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller"]
            display_name = f"{random.choice(first_names)} {random.choice(last_names)}"
    
    conversation_id = generate_conversation_id()
    
    # Generate participants
    participants = []
    if is_group_chat:
        participant_count = random.randint(3, 6)
        for _ in range(participant_count):
            participants.append({
                "name": f"{random.choice(['John', 'Sarah', 'Mike', 'Emma', 'David', 'Lisa'])} {random.choice(['S', 'J', 'W', 'B', 'J', 'M'])}.",
                "id": f"person:{uuid.uuid4()}"
            })
    else:
        participants = [{
            "name": display_name,
            "id": f"person:{uuid.uuid4()}"
        }]
    
    # Add myself to participants
    participants.append({
        "name": "Me",
        "id": "me"
    })
    
    # Generate messages
    messages = []
    for i in range(message_count):
        is_from_me = random.choice([True, False])
        messages.append(generate_message(
            is_from_me=is_from_me,
            days_ago=i // 3,  # Spread messages over a few days
            conversation_id=conversation_id
        ))
    
    # Sort messages by date
    messages.sort(key=lambda m: m["date"])
    
    return {
        "id": conversation_id,
        "display_name": display_name,
        "is_group_chat": is_group_chat,
        "participants": participants,
        "last_message": messages[-1] if messages else None,
        "unread_count": random.randint(0, 3),
        "messages": messages
    }


def generate_contact(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    phone_numbers: Optional[List[Dict[str, str]]] = None,
    emails: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Generate a realistic contact object for testing.
    
    Args:
        first_name (str, optional): First name of the contact.
        last_name (str, optional): Last name of the contact.
        phone_numbers (list, optional): List of phone number objects.
        emails (list, optional): List of email objects.
        
    Returns:
        dict: A contact object with realistic properties
    """
    if first_name is None:
        first_names = ["John", "Sarah", "Mike", "Emma", "David", "Lisa", "James", "Emily"]
        first_name = random.choice(first_names)
    
    if last_name is None:
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Wilson"]
        last_name = random.choice(last_names)
    
    if phone_numbers is None:
        phone_number_count = random.randint(1, 3)
        phone_numbers = []
        labels = ["mobile", "home", "work", "iPhone", "main"]
        
        for _ in range(phone_number_count):
            phone_numbers.append({
                "label": random.choice(labels),
                "value": f"+1{random.randint(1000000000, 9999999999)}"
            })
    
    if emails is None:
        email_count = random.randint(0, 2)
        emails = []
        domains = ["gmail.com", "yahoo.com", "outlook.com", "icloud.com", "company.com"]
        labels = ["home", "work", "other"]
        
        for _ in range(email_count):
            domain = random.choice(domains)
            email_addr = f"{first_name.lower()}.{last_name.lower()}@{domain}"
            emails.append({
                "label": random.choice(labels),
                "value": email_addr
            })
    
    return {
        "id": str(uuid.uuid4()),
        "display_name": f"{first_name} {last_name}",
        "first_name": first_name,
        "last_name": last_name,
        "phones": phone_numbers,
        "emails": emails
    }


def generate_email(
    subject: Optional[str] = None,
    body: Optional[str] = None,
    sender: Optional[Dict[str, str]] = None,
    recipients: Optional[List[Dict[str, str]]] = None,
    is_read: bool = True,
    has_attachments: bool = False
) -> Dict[str, Any]:
    """
    Generate a realistic email object for testing.
    
    Args:
        subject (str, optional): Email subject line.
        body (str, optional): Email body content.
        sender (dict, optional): Sender information.
        recipients (list, optional): List of recipient information.
        is_read (bool, optional): Whether the email has been read. Default is True.
        has_attachments (bool, optional): Whether the email has attachments. Default is False.
        
    Returns:
        dict: An email object with realistic properties
    """
    if subject is None:
        subjects = [
            "Meeting tomorrow",
            "Project update",
            "Question about the report",
            "Invitation: Team lunch",
            "Weekly summary",
            "Important announcement",
            "Follow-up on our discussion",
            "Your account statement",
            "New policy update",
            "Reminder: deadline approaching"
        ]
        subject = random.choice(subjects)
    
    if body is None:
        bodies = [
            "Hi there,\n\nJust wanted to check in about the project status. Let me know when you have a moment.\n\nThanks,\nJohn",
            "Hello,\n\nI've attached the latest report for your review. Please let me know if you have any questions.\n\nBest regards,\nSarah",
            "Team,\n\nReminder that we have a meeting scheduled for tomorrow at 2pm. Please come prepared with your updates.\n\nThanks,\nDavid",
            "Hi,\n\nJust following up on our conversation earlier. I've made the changes you suggested.\n\nRegards,\nEmma",
            "Hello everyone,\n\nPlease note that the office will be closed on Monday for the holiday.\n\nThanks,\nManagement"
        ]
        body = random.choice(bodies)
    
    if sender is None:
        domains = ["company.com", "gmail.com", "outlook.com", "example.org"]
        first_names = ["John", "Sarah", "David", "Emma", "Michael"]
        last_names = ["Smith", "Johnson", "Brown", "Davis", "Wilson"]
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        email = f"{name.lower().replace(' ', '.')}@{random.choice(domains)}"
        sender = {
            "name": name,
            "address": email
        }
    
    if recipients is None:
        recipient_count = random.randint(1, 3)
        recipients = []
        domains = ["company.com", "gmail.com", "outlook.com", "example.org"]
        
        for _ in range(recipient_count):
            first_name = random.choice(["Alice", "Bob", "Charlie", "Diana", "Edward"])
            last_name = random.choice(["Anderson", "Baker", "Clark", "Davis", "Evans"])
            name = f"{first_name} {last_name}"
            email = f"{name.lower().replace(' ', '.')}@{random.choice(domains)}"
            recipients.append({
                "name": name,
                "address": email
            })
    
    attachments = []
    if has_attachments:
        attachment_count = random.randint(1, 3)
        file_types = [".pdf", ".docx", ".pptx", ".xlsx", ".jpg", ".png", ".txt"]
        file_names = ["Report", "Presentation", "Document", "Spreadsheet", "Image", "Notes", "Proposal"]
        
        for _ in range(attachment_count):
            file_name = f"{random.choice(file_names)}{random.choice(file_types)}"
            attachments.append({
                "name": file_name,
                "size": random.randint(10000, 5000000),
                "type": f"application/{file_name.split('.')[-1]}"
            })
    
    return {
        "id": str(uuid.uuid4()),
        "subject": subject,
        "body": body,
        "sender": sender,
        "recipients": recipients,
        "date": generate_timestamp(days_ago=random.randint(0, 10)),
        "is_read": is_read,
        "attachments": attachments,
        "folder": random.choice(["INBOX", "Sent", "Archive", "Important"]),
        "flags": []
    }


def generate_process_info(
    name: Optional[str] = None,
    args: Optional[List[str]] = None,
    user: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a realistic process information object for testing.
    
    Args:
        name (str, optional): Process name.
        args (list, optional): Process arguments.
        user (str, optional): User running the process.
        
    Returns:
        dict: A process information object with realistic properties
    """
    if name is None:
        process_names = ["Messages", "Mail", "Finder", "Safari", "Chrome", "Terminal", "python", "node", "systemd", "launchd"]
        name = random.choice(process_names)
    
    if args is None:
        args = []
        if name == "python":
            args = ["main.py", "--debug"]
        elif name == "node":
            args = ["server.js"]
    
    if user is None:
        user = random.choice(["root", "admin", "shugo", "system"])
    
    return {
        "pid": random.randint(1000, 50000),
        "name": name,
        "user": user,
        "command": name,
        "full_command": f"{name} {' '.join(args)}" if args else name,
        "cpu_percent": round(random.uniform(0.1, 15.0), 1),
        "memory_percent": round(random.uniform(0.1, 8.0), 1),
        "create_time": generate_timestamp(days_ago=random.randint(0, 5)),
        "args": args,
        "status": random.choice(["running", "sleeping"]),
        "parent_pid": random.randint(1, 999),
        "children": []
    }


def generate_file_entry(
    name: Optional[str] = None,
    is_directory: bool = False,
    days_ago: int = 0
) -> Dict[str, Any]:
    """
    Generate a realistic file or directory entry for testing.
    
    Args:
        name (str, optional): File or directory name.
        is_directory (bool, optional): Whether it's a directory. Default is False.
        days_ago (int, optional): When the file was last modified. Default is 0.
        
    Returns:
        dict: A file or directory entry with realistic properties
    """
    if name is None:
        if is_directory:
            directory_names = ["Documents", "Pictures", "Music", "Videos", "Projects", "Downloads", "Desktop", "Applications"]
            name = random.choice(directory_names)
        else:
            file_bases = ["document", "report", "presentation", "notes", "image", "data", "config", "backup"]
            file_extensions = [".txt", ".pdf", ".doc", ".docx", ".jpg", ".png", ".json", ".py", ".js", ".html", ".css", ".md"]
            name = f"{random.choice(file_bases)}{random.choice(file_extensions)}"
    
    entry_type = "directory" if is_directory else "file"
    size = 0 if is_directory else random.randint(1024, 10485760)  # 1KB to 10MB
    
    return {
        "name": name,
        "type": entry_type,
        "size": size,
        "modified": generate_timestamp(days_ago=days_ago)
    }
