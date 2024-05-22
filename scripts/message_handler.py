import json
import time
import hashlib


def create_checksum(message_dict):
    message_str = json.dumps(message_dict, sort_keys=True)
    return hashlib.sha256(message_str.encode()).hexdigest()


def create_message(type, content, time_sent=None, checksum=None):
    if time_sent is None:
        time_sent = time.strftime("%H:%M:%S")
    message = {
        "type": type,
        "content": content,
        "time_sent": time_sent,
    }
    if checksum is None:
        checksum = create_checksum(message)
    message["checksum"] = checksum
    return json.dumps(message)


def parse_message(message_str):
    message_dict = json.loads(message_str)
    received_checksum = message_dict.pop("checksum", None)
    if received_checksum is None:
        raise ValueError("No checksum found in the message.")

    calculated_checksum = create_checksum(message_dict)
    if received_checksum != calculated_checksum:
        raise ValueError("Checksum does not match. The message may be corrupted.")

    message_dict["checksum"] = received_checksum
    return message_dict


def send_message(socket, msg_type, content):
    message_str = create_message(msg_type, content)
    socket.sendall(message_str.encode())


def receive_message(socket):
    data = socket.recv(1024).decode()
    if data:
        return parse_message(data)
    return None
