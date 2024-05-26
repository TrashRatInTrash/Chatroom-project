import time
import hashlib
import asyncio
from scapy.all import *
from CONSTANTS import MessageType

DELAY = 0.2

MessageTypeMapping = {
    MessageType.COMMAND: 0,
    MessageType.MESSAGE: 1,
    MessageType.ACK: 2,
    MessageType.NACK: 3,
    MessageType.RESP: 4,
    MessageType.INFO: 5,
}


class ChatPacket(Packet):
    name = "ChatPacket"
    fields_desc = [
        ByteEnumField("type", 0, MessageTypeMapping),
        ShortField("seq_num", 0),
        ShortField("content_length", 0),
        StrLenField("content", "", length_from=lambda pkt: pkt.content_length),
        StrFixedLenField("checksum", "", 64),
    ]


def create_checksum(pkt_type, seq_num, content_length, content):
    packet_str = f"{pkt_type}{seq_num}{content_length}{content}"
    return hashlib.sha256(packet_str.encode()).hexdigest()


def create_message(msg_type, content, seq_num, time_sent=None):
    time.sleep(DELAY)
    try:
        print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
        print("Entered create_message function")
        print(
            f"msg_type: {msg_type}, content: {content}, seq_num: {seq_num}, time_sent: {time_sent}"
        )

        if time_sent is None:
            time_sent = time.strftime("%H:%M:%S")

        packet = ChatPacket(
            type=MessageTypeMapping[msg_type],
            seq_num=seq_num,
            content_length=len(content),
            content=content,
        )

        checksum = create_checksum(
            packet.type, packet.seq_num, packet.content_length, packet.content
        )
        packet.checksum = checksum.encode()

        print(
            f"Created message packet:\nType: {packet.type}\nSeq Num: {packet.seq_num}\nContent Length: {packet.content_length}\nContent: {packet.content}\nChecksum: {packet.checksum.decode()}"
        )
        print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
        return packet
    except Exception as e:
        print(f"Exception in create_message: {e}")
        raise


def parse_message(data):
    time.sleep(DELAY)
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    print("Entered parse_message function")
    packet = ChatPacket(data)
    print(
        f"Parsed raw message packet:\nType: {packet.type}\nSeq Num: {packet.seq_num}\nContent Length: {packet.content_length}\nContent: {packet.content}\nChecksum: {packet.checksum.decode()}"
    )
    received_checksum = packet.checksum.decode()
    calculated_checksum = create_checksum(
        packet.type, packet.seq_num, packet.content_length, packet.content
    )
    print(f"Calculated checksum: {calculated_checksum}")
    if received_checksum != calculated_checksum:
        raise ValueError("Checksum does not match. The message may be corrupted.")
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    return packet


async def send_message(writer, msg_type, content, seq_num):
    time.sleep(DELAY)
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    print("Entered send_message function")
    address = writer.get_extra_info("peername")
    print(f"Address: {address}")
    packet = create_message(msg_type, content, seq_num)
    print(
        f"Sending message packet:\nType: {packet.type}\nSeq Num: {packet.seq_num}\nContent Length: {packet.content_length}\nContent: {packet.content}\nChecksum: {packet.checksum.decode()}"
    )
    writer.write(bytes(packet))
    await writer.drain()
    print(
        f"Sent message packet:\nType: {packet.type}\nSeq Num: {packet.seq_num}\nContent Length: {packet.content_length}\nContent: {packet.content}\nChecksum: {packet.checksum.decode()}"
    )
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")


async def receive_message(reader, expected_seq_num):
    time.sleep(DELAY)
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    print("Entered receive_message function")
    data = await reader.read(1024)
    print(f"\nRaw data received: {data}\n")
    message = parse_message(data)
    if message.seq_num != expected_seq_num:
        if message.type == MessageTypeMapping[MessageType.NACK]:
            print(f"Received NACK for seq_num {message.seq_num}, retransmitting...")
            return message  # Return the NACK message without raising an error
        raise ValueError(
            f"Sequence number mismatch, expected {expected_seq_num} received {message.seq_num}"
        )
    print(
        f"Processed message packet:\nType: {message.type}\nSeq Num: {message.seq_num}\nContent Length: {message.content_length}\nContent: {message.content}\nChecksum: {message.checksum.decode()}"
    )
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    return message


async def send_nack(writer, expected_seq_num):
    time.sleep(DELAY)
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    print("Entered send_nack function")
    nack_message = create_message(
        MessageType.NACK, f"NACK for {expected_seq_num}", expected_seq_num
    )
    writer.write(bytes(nack_message))
    await writer.drain()
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
