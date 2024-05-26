import asyncio
import message_handler
from CONSTANTS import MessageType
import json
import threading

client_seq_num = 0
server_seq_num = 0
running = True
sent_packets = {}  # Store sent packets for potential retransmission
username_set = False

MessageTypeMapping = {
    MessageType.COMMAND: 0,
    MessageType.MESSAGE: 1,
    MessageType.ACK: 2,
    MessageType.NACK: 3,
    MessageType.RESP: 4,
    MessageType.INFO: 5,
}

ReverseMessageTypeMapping = {v: k for k, v in MessageTypeMapping.items()}


async def send_message(writer, msg_type, content):
    global client_seq_num
    packet = message_handler.create_message(msg_type, content, client_seq_num)
    sent_packets[client_seq_num] = packet  # Store the packet
    writer.write(bytes(packet))
    await writer.drain()
    client_seq_num += 1


async def receive_message(reader, writer):
    global server_seq_num
    global running
    try:
        while running:
            packet = await message_handler.receive_message(reader, server_seq_num)
            packet_type = ReverseMessageTypeMapping.get(packet.type)

            if packet_type == MessageType.NACK:
                expected_seq_num = int(packet.content.split()[-1])
                if expected_seq_num in sent_packets:
                    await retransmit_packet(writer, sent_packets[expected_seq_num])
                continue  # Do not increment server_seq_num on NACK

            if packet.seq_num != server_seq_num:
                await send_nack(writer, server_seq_num)
                continue

            server_seq_num += 1
            print(f"Received: {packet.content}")
    except Exception as e:
        print(f"Error receiving message: {e}")


async def send_nack(writer, expected_seq_num):
    nack_message = message_handler.create_message(
        MessageType.NACK, f"NACK for {expected_seq_num}", expected_seq_num
    )
    writer.write(bytes(nack_message))
    await writer.drain()


async def retransmit_packet(writer, packet):
    writer.write(bytes(packet))
    await writer.drain()


def handle_user_input(writer):
    global running
    global username_set
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Set username
    username = input("Enter username: ")
    loop.run_until_complete(
        send_message(writer, MessageType.COMMAND, f"/username {username}")
    )
    username_set = True

    while running:
        message = input("Enter message: ")
        if message.startswith("/"):
            command = message.strip()
            if command == "/qqq":
                loop.run_until_complete(
                    send_message(writer, MessageType.COMMAND, command)
                )
                running = False
                break
            elif command.startswith("/create"):
                loop.run_until_complete(
                    send_message(writer, MessageType.COMMAND, command)
                )
            elif command.startswith("/join"):
                loop.run_until_complete(
                    send_message(writer, MessageType.COMMAND, command)
                )
            elif command.startswith("/leave"):
                loop.run_until_complete(
                    send_message(writer, MessageType.COMMAND, command)
                )
            elif command == "/wrong":
                loop.run_until_complete(
                    send_message_with_incorrect_checksum(writer, MessageType.MESSAGE, "Test message with incorrect checksum")
                )
            elif command == "/users":
                loop.run_until_complete(
                    send_message(writer, MessageType.COMMAND, command)
                )
            else:
                print("Unknown command")
        else:
            loop.run_until_complete(send_message(writer, MessageType.MESSAGE, message))


async def send_message_with_incorrect_checksum(writer, msg_type, content):
    global client_seq_num
    packet = message_handler.create_message(msg_type, content, client_seq_num)
    packet.checksum = b"incorrect_checksum"  # Intentionally set an incorrect checksum
    writer.write(bytes(packet))
    await writer.drain()
    client_seq_num += 1


async def main():
    global running
    reader, writer = await asyncio.open_connection("192.168.28.83", 5555)
    print("Connected to server")

    input_thread = threading.Thread(target=handle_user_input, args=(writer,))
    input_thread.start()

    await receive_message(reader, writer)

    print("Closing connection")
    writer.close()
    await writer.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
