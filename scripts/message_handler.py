import json
import time

# Function to create a message
def create_message(type, content, time_sent=None, time_received=None):
    if time_sent is None:
        time_sent = time.strftime('%H:%M:%S')
    message = {
        "type": type,
        "content": content,
        "time_sent": time_sent,
    }
    return json.dumps(message)

# Function to parse a message string into a message dictionary
def parse_message(message_str):
    return json.loads(message_str)
