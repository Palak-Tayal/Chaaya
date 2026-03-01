import re

def parse_whatsapp_chat(filepath):
    """
    Parses a WhatsApp chat .txt file, filtering out media omitted and system messages.
    Returns a list of dicts: [{'timestamp':..., 'sender':..., 'message':...}]
    """
    messages = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # Skip system messages
            if "Messages and calls are end-to-end encrypted" in line:
                continue
            
            # Skip lines with media omitted
            if "<Media omitted>" in line:
                continue
            
            # Split timestamp and the rest
            if ' - ' not in line:
                continue
            timestamp_part, rest = line.split(' - ', 1)
            
            # Split sender and message
            if ': ' not in rest:
                continue
            sender, message = rest.split(': ', 1)
            
            # Clean sender and message
            sender = sender.strip()
            message = message.strip()
            
            # Skip if message is empty after cleaning
            if not message:
                continue
            
            messages.append({
                'timestamp': timestamp_part.strip(),
                'sender': sender,
                'message': message
            })
    return messages