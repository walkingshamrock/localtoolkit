# Integration Patterns

This guide provides examples of common workflows that combine multiple LocalToolKit app integrations.

## Finding Messages from a Named Contact

```python
from localtoolkit.contacts.search_by_name import search_by_name_logic
from localtoolkit.messages.list_conversations import list_conversations_logic
from localtoolkit.messages.get_messages import get_messages_logic

# 1. Find contact by name
contact_result = search_by_name_logic(name="John")

if contact_result["success"] and contact_result["contacts"]:
    contact = contact_result["contacts"][0]

    # 2. Get phone number
    if "phones" in contact and contact["phones"]:
        phone = contact["phones"][0]["number"]

        # 3. Find the conversation with this contact
        convos_result = list_conversations_logic()

        if convos_result["success"]:
            target_convo = None
            for convo in convos_result["conversations"]:
                if phone in convo["id"]:
                    target_convo = convo
                    break

            # 4. Get messages from the conversation
            if target_convo:
                messages = get_messages_logic(
                    conversation_id=target_convo["id"],
                    limit=10
                )
```

## Sending a Message to a Contact

```python
from localtoolkit.contacts.search_by_name import search_by_name_logic
from localtoolkit.messages.send_message import send_message_logic

# 1. Find contact by name
contact_result = search_by_name_logic(name="Jane")

if contact_result["success"] and contact_result["contacts"]:
    contact = contact_result["contacts"][0]

    # 2. Get phone number
    if "phones" in contact and contact["phones"]:
        phone = contact["phones"][0]["number"]

        # 3. Construct conversation ID
        conversation_id = f"iMessage;-;{phone}"

        # 4. Send the message
        send_result = send_message_logic(
            conversation_id=conversation_id,
            text="Hello from LocalToolKit!"
        )
```

## Launching an Application and Monitoring It

```python
from apps.process.start_process import start_process_logic
from apps.process.monitor_process import monitor_process_logic

# 1. Start the application
start_result = start_process_logic(
    command="open",
    args=["-a", "Safari", "https://www.apple.com"],
    background=True
)

if start_result["success"]:
    # 2. Wait a moment for app to initialize
    import time
    time.sleep(2)

    # 3. Monitor the process
    monitor_result = monitor_process_logic(
        pid=start_result["pid"],
        duration=10.0,
        interval=1.0
    )

    # 4. Analyze the results
    if monitor_result["success"]:
        cpu = monitor_result["summary"]["cpu_percent"]["avg"]
        memory = monitor_result["summary"]["memory_percent"]["avg"]
        print(f"Safari used {cpu}% CPU and {memory}% memory on average")
```

## Working with Files and Mail

```python
from apps.filesystem.read_file import read_file_logic
from apps.mail.send_mail import send_mail_logic

# 1. Read a file
file_result = read_file_logic(
    path="/Users/username/Documents/report.txt"
)

if file_result["success"]:
    # 2. Send the content via email
    mail_result = send_mail_logic(
        to=["recipient@example.com"],
        subject="File Content",
        body=f"Here's the content of the file:\n\n{file_result['content']}",
        attachments=["/Users/username/Documents/report.txt"]
    )
```

## Best Practices

When combining different app integrations, follow these best practices:

- Handle errors at each integration point
- Validate data before passing between integrations
- Provide clear error messages when integration fails
- Use AppleScript runner consistently via `apps/applescript/utils/applescript_runner.py`
- Test each integration independently before combining them
