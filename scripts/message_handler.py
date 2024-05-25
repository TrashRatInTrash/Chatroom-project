import json
import time
import hashlib
import asyncio
from CONSTANTS import MessageType

DELAY = 0.2


def create_checksum(message_dict):
    message_str = json.dumps(message_dict, sort_keys=True)
    return hashlib.sha256(message_str.encode()).hexdigest()


def create_message(msg_type, content, seq_num, time_sent=None):
    if time_sent is None:
        time_sent = time.strftime("%H:%M:%S")
    message = {
        "type": msg_type.value,
        "content": content,
        "time_sent": time_sent,
        "seq_num": seq_num,
    }
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


async def send_message(writer, msg_type, content, seq_num):
    address = writer.get_extra_info("peername")
    print(f"{address}")
    message_str = create_message(msg_type, content, seq_num)
    print(
        f"\n~~~~~~~~~~~~~~~~~~~~~~~~~~~\nSending message: {message_str} to {address}\n~~~~~~~~~~~~~~~~~~~~~~~~~~~\n"
    )  # Debugging statement
    writer.write(message_str.encode() + b"\n")
    await writer.drain()
    print(
        f"\n~~~~~~~~~~~~~~~~~~~~~~~~~~~\nSent: {message_str}\n~~~~~~~~~~~~~~~~~~~~~~~~~~~\n"
    )


async def receive_message(reader, expected_seq_num):

    data = await reader.readuntil(b"\n")
    message_str = data.decode().strip()

    print(
        f"\n~~~~~~~~~~~~~~~~~~~~~~~~~~~\nReceived raw message: {message_str} \n~~~~~~~~~~~~~~~~~~~~~~~~~~~\n"
    )  # Debugging statement
    message = parse_message(message_str)
    if message["seq_num"] != expected_seq_num:
        raise ValueError(f"Sequence number mismatch, expected {expected_seq_num} received {message['seq_num']}")
    print(
        f"\n~~~~~~~~~~~~~~~~~~~~~~~~~~~\nProcessed message: {message}\n~~~~~~~~~~~~~~~~~~~~~~~~~~~\n"
    )  # Debugging statement
    return message
