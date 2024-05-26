import asyncio
import message_handler
from CONSTANTS import MessageType

clients = {}
client_seq_nums = {}
server_seq_nums = {}
rooms = {}
sent_packets = {}  # Store sent packets for potential retransmission

MessageTypeMapping = {
    MessageType.COMMAND: 0,
    MessageType.MESSAGE: 1,
    MessageType.ACK: 2,
    MessageType.NACK: 3,
    MessageType.RESP: 4,
    MessageType.INFO: 5,
}

ReverseMessageTypeMapping = {v: k for k, v in MessageTypeMapping.items()}


def return_command_code(command):
    if command == "/qqq":
        return 1
    if command.startswith("/create"):
        return 2
    if command.startswith("/join"):
        return 3
    if command.startswith("/leave"):
        return 4
    if command == "/wrong":
        return 5
    if command.startswith("/username"):
        return 6
    if command == "/users":
        return 8


async def handle_client(reader, writer):
    address = writer.get_extra_info("peername")
    print(f"\nAccepted connection from {address}\n")

    client_seq_nums[address] = 0
    server_seq_nums[address] = 0
    username = None
    current_room = None

    try:
        await message_handler.send_message(
            writer,
            MessageType.INFO,
            "Please set your username with /username <your_username>",
            client_seq_nums[address],
        )
        client_seq_nums[address] += 1

        while True:
            try:
                packet = await message_handler.receive_message(
                    reader, server_seq_nums[address]
                )
                server_seq_nums[address] += 1

                content = (
                    packet.content.decode()
                    if isinstance(packet.content, bytes)
                    else packet.content
                )
                packet_type = ReverseMessageTypeMapping.get(packet.type)

                if packet_type == MessageType.COMMAND:
                    command = content.strip()
                    code = return_command_code(command)

                    if code == 6:  # Set username
                        _, username = command.split(maxsplit=1)
                        clients[address] = username
                        await send_and_store_message(
                            writer,
                            MessageType.RESP,
                            f"Username set to {username}",
                            client_seq_nums[address],
                        )
                        client_seq_nums[address] += 1
                        break
                    else:
                        await send_and_store_message(
                            writer,
                            MessageType.RESP,
                            "Please set your username first using /username <your_username>",
                            client_seq_nums[address],
                        )
                        client_seq_nums[address] += 1
            except ValueError as e:
                await message_handler.send_nack(writer, server_seq_nums[address])

        while True:
            try:
                packet = await message_handler.receive_message(
                    reader, server_seq_nums[address]
                )
                server_seq_nums[address] += 1

                content = (
                    packet.content.decode()
                    if isinstance(packet.content, bytes)
                    else packet.content
                )
                packet_type = ReverseMessageTypeMapping.get(packet.type)

                if packet_type == MessageType.COMMAND:
                    command = content.strip()
                    code = return_command_code(command)

                    if code == 1:  # Hard disconnect
                        await send_and_store_message(
                            writer,
                            MessageType.RESP,
                            "Disconnecting",
                            client_seq_nums[address],
                        )
                        client_seq_nums[address] += 1
                        break
                    elif code == 2:  # Create room
                        room_id = f"room_{len(rooms) + 1}"
                        rooms[room_id] = [writer]
                        current_room = room_id
                        await send_and_store_message(
                            writer,
                            MessageType.RESP,
                            f"Created and joined room {room_id}",
                            client_seq_nums[address],
                        )
                        client_seq_nums[address] += 1
                    elif code == 3:  # Join room
                        _, room_id = command.split()
                        if room_id in rooms:
                            rooms[room_id].append(writer)
                            current_room = room_id
                            await send_and_store_message(
                                writer,
                                MessageType.RESP,
                                f"Joined room {room_id}",
                                client_seq_nums[address],
                            )
                            client_seq_nums[address] += 1
                        else:
                            await send_and_store_message(
                                writer,
                                MessageType.RESP,
                                "Room does not exist",
                                client_seq_nums[address],
                            )
                            client_seq_nums[address] += 1
                    elif code == 4:  # Leave room
                        if current_room and writer in rooms[current_room]:
                            rooms[current_room].remove(writer)
                            current_room = None
                            await send_and_store_message(
                                writer,
                                MessageType.RESP,
                                "Left the room",
                                client_seq_nums[address],
                            )
                            client_seq_nums[address] += 1
                        else:
                            await send_and_store_message(
                                writer,
                                MessageType.RESP,
                                "Not in any room",
                                client_seq_nums[address],
                            )
                            client_seq_nums[address] += 1
                    elif code == 5:  # Send incorrect checksum
                        await send_and_store_message(
                            writer,
                            MessageType.COMMAND,
                            "This message has an incorrect checksum",
                            client_seq_nums[address],
                        )
                        client_seq_nums[address] += 1
                    elif code == 8:  # List users
                        user_list = ", ".join(clients.values())
                        await send_and_store_message(
                            writer,
                            MessageType.RESP,
                            f"Online users: {user_list}",
                            client_seq_nums[address],
                        )
                        client_seq_nums[address] += 1
                elif packet_type == MessageType.NACK:
                    expected_seq_num = int(content.split()[-1])
                    await retransmit_packet(writer, expected_seq_num)
                else:
                    if current_room:
                        await broadcast(content, username, current_room)
                        await send_and_store_message(
                            writer,
                            MessageType.ACK,
                            "Message received",
                            client_seq_nums[address],
                        )
                        client_seq_nums[address] += 1
                    else:
                        await send_and_store_message(
                            writer,
                            MessageType.RESP,
                            "You are not in a room. Use /create or /join to enter a room.",
                            client_seq_nums[address],
                        )
                        client_seq_nums[address] += 1
            except ValueError as e:
                await message_handler.send_nack(writer, server_seq_nums[address])
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        if current_room and writer in rooms.get(current_room, []):
            rooms[current_room].remove(writer)
        writer.close()
        await writer.wait_closed()
        if address in clients:
            del clients[address]
        if address in client_seq_nums:
            del client_seq_nums[address]
        if address in server_seq_nums:
            del server_seq_nums[address]
        print(f"Connection with {address} closed")


async def send_and_store_message(writer, msg_type, content, seq_num):
    packet = message_handler.create_message(msg_type, content, seq_num)
    sent_packets[(writer.get_extra_info("peername"), seq_num)] = (
        packet  # Store the packet
    )
    writer.write(bytes(packet))
    await writer.drain()


async def retransmit_packet(writer, seq_num):
    packet_key = (writer.get_extra_info("peername"), seq_num)
    if packet_key in sent_packets:
        writer.write(bytes(sent_packets[packet_key]))
        await writer.drain()


async def broadcast(content, username, room_id):
    for client in rooms.get(room_id, []):
        client_address = client.get_extra_info("peername")
        await send_and_store_message(
            client,
            MessageType.MESSAGE,
            f"{username}: {content}",
            client_seq_nums[client_address],
        )
        client_seq_nums[client_address] += 1


async def main():
    server = await asyncio.start_server(handle_client, "0.0.0.0", 5555)
    print("Server listening on 0.0.0.0:5555")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
