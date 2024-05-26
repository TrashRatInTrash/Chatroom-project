import asyncio
import message_handler
from CONSTANTS import MessageType
import threading

client_seq_num = 0
server_seq_num = 0
running = True
sent_packets = {}

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
    sent_packets[client_seq_num] = packet
    print(
        f"Stored packet with seq_num {client_seq_num} in sent_packets: {packet.summary()}"
    )
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
                print(f" seq num from nack {expected_seq_num}")
                await retransmit_packet(writer, expected_seq_num)
                continue

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


async def retransmit_packet(writer, seq_num):
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    print(f"Entered retransmit_packet function for seq_num {seq_num}")
    for key, packet in sent_packets.items():
        print(f"Seq Num: {key}, Packet: {packet.content}")
    if seq_num in sent_packets:
        packet = sent_packets[seq_num]
        print(
            f"Retransmitting packet:\nType: {packet.type}\nSeq Num: {packet.seq_num}\nContent Length: {packet.content_length}\nContent: {packet.content}\nChecksum: {packet.checksum.decode()}"
        )
        writer.write(bytes(packet))
        await writer.drain()
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")


def handle_user_input(writer):
    global running
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    username = input("Enter username: ")
    loop.run_until_complete(
        send_message(writer, MessageType.COMMAND, f"/username {username}")
    )

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
                    send_message_with_incorrect_checksum(
                        writer,
                        MessageType.MESSAGE,
                        "Test message with incorrect checksum",
                    )
                )
            elif command == "/users":
                loop.run_until_complete(
                    send_message(writer, MessageType.COMMAND, command)
                )
            elif command.startswith("/kick"):
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
    sent_packets[client_seq_num] = packet  # Store the packet first
    print(
        f"Stored packet with seq_num {client_seq_num} in sent_packets (before modifying checksum): {packet.summary()}"
    )
    packet.checksum = b"incorrect_checksum"  # Modify the checksum
    writer.write(bytes(packet))
    await writer.drain()
    client_seq_num += 1


async def main():
    global running
    reader, writer = await asyncio.open_connection("127.0.0.1", 5555)
    print("Connected to server")

    input_thread = threading.Thread(target=handle_user_input, args=(writer,))
    input_thread.start()

    await receive_message(reader, writer)

    print("Closing connection")
    writer.close()
    await writer.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
