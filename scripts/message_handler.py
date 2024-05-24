import json
import time
import hashlib
import socket
from CONSTANTS import MessageType

# Configurable timeout values
SEND_TIMEOUT = 2  # seconds
RECEIVE_TIMEOUT = 2  # seconds
DELAY = 0.5  # delay in seconds for send and receive operations


def create_checksum(message_dict):
    message_str = json.dumps(message_dict, sort_keys=True)
    return hashlib.sha256(message_str.encode()).hexdigest()


def create_message(msg_type, content, seq_num, time_sent=None, checksum=None):
    if time_sent is None:
        time_sent = time.strftime("%H:%M:%S")
    message = {
        "type": msg_type.value,
        "content": content,
        "time_sent": time_sent,
        "seq_num": seq_num,
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


def send_message(sock, msg_type, content, seq_num):
    message_str = create_message(msg_type, content, seq_num)
    ack_received = False

    while not ack_received:
        try:
            print(f"\n~~~~~~~~~~~~~~~~\nSENDING {message_str}")
            sock.sendall(message_str.encode())
            time.sleep(DELAY)  # Delay for 0.5 seconds
            sock.settimeout(SEND_TIMEOUT)
            ack_message_str = sock.recv(1024).decode()
            ack_message = parse_message(ack_message_str)
            if (
                ack_message["type"] == MessageType.ACK.value
                and ack_message["seq_num"] == seq_num
            ):
                print(f"ACK received for seq_num: {seq_num}")
                ack_received = True
            else:
                print(f"Unexpected ACK: {ack_message}")
        except socket.timeout:
            print("Timeout! Resending message.")
        except BrokenPipeError:
            print("Connection closed by the server.")
            break
        except Exception as e:
            print(f"Exception while sending message: {e}")
            break


def receive_message(sock, expected_seq_num):
    while True:
        try:
            sock.settimeout(RECEIVE_TIMEOUT)
            data = sock.recv(1024).decode()
            if data:
                message = parse_message(data)
                print(f"\n~~~~~~~~~~~~~~~~\nRECEIVED {message}")
                time.sleep(DELAY)  # Delay for 0.5 seconds
                if message["seq_num"] == expected_seq_num:
                    ack_message_str = create_message(
                        MessageType.ACK, "", message["seq_num"]
                    )
                    sock.sendall(ack_message_str.encode())
                    return message
                else:
                    print(
                        f"Unexpected seq_num: {message['seq_num']} (expected: {expected_seq_num})"
                    )
                    ack_message_str = create_message(
                        MessageType.ACK, "", expected_seq_num - 1
                    )
                    sock.sendall(ack_message_str.encode())
        except socket.timeout:
            continue
        except BrokenPipeError:
            print("Connection closed by the client.")
            break
        except Exception as e:
            print(f"Exception while receiving message: {e}")
            break
