import asyncio
import message_handler
from CONSTANTS import MessageType

clients = {}
client_seq_nums = {}
server_seq_nums = {}
rooms = {}
sent_packets = {}
nack_retries = {}

NACK_LIMIT = 5

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
    if command.startswith("/kick"):
        return 9


async def handle_client(reader, writer):
    address = writer.get_extra_info("peername")
    client_seq_nums[address] = 0
    server_seq_nums[address] = 0
    nack_retries[address] = {}
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
                packet_type = ReverseMessageTypeMapping.get(packet.type)

                if packet_type == MessageType.NACK:
                    expected_seq_num = int(packet.content.split()[-1])
                    await retransmit_packet(writer, expected_seq_num)
                    continue

                if packet.seq_num != server_seq_nums[address]:
                    await handle_nack(writer, address, server_seq_nums[address])
                    continue

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
                await handle_nack(writer, address, server_seq_nums[address])

        while True:
            try:
                packet = await message_handler.receive_message(
                    reader, server_seq_nums[address]
                )
                packet_type = ReverseMessageTypeMapping.get(packet.type)

                if packet_type == MessageType.NACK:
                    expected_seq_num = int(packet.content.split()[-1])
                    await retransmit_packet(writer, expected_seq_num)
                    continue

                if packet.seq_num != server_seq_nums[address]:
                    await handle_nack(writer, address, server_seq_nums[address])
                    continue

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
                    elif code == 9:  # Kick user
                        target_username = command.split()[1]
                        await kick_user(target_username)
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
                await handle_nack(writer, address, server_seq_nums[address])
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
        if address in nack_retries:
            del nack_retries[address]
        print(f"Connection with {address} closed")


async def send_and_store_message(writer, msg_type, content, seq_num):
    packet = message_handler.create_message(msg_type, content, seq_num)
    sent_packets[(writer.get_extra_info("peername"), seq_num)] = packet
    writer.write(bytes(packet))
    await writer.drain()


async def retransmit_packet(writer, seq_num):
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    print(f"Entered retransmit_packet function for seq_num {seq_num}")
    packet_key = (writer.get_extra_info("peername"), seq_num)
    if packet_key in sent_packets:
        packet = sent_packets[packet_key]
        print(
            f"Retransmitting packet:\nType: {packet.type}\nSeq Num: {packet.seq_num}\nContent Length: {packet.content_length}\nContent: {packet.content}\nChecksum: {packet.checksum.decode()}"
        )
        writer.write(bytes(packet))
        await writer.drain()
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")


async def handle_nack(writer, address, seq_num):
    if address not in nack_retries:
        nack_retries[address] = {}
    if seq_num not in nack_retries[address]:
        nack_retries[address][seq_num] = 0

    nack_retries[address][seq_num] += 1

    if nack_retries[address][seq_num] <= NACK_LIMIT:
        await message_handler.send_nack(writer, seq_num)
    else:
        print(f"Too many NACKs for {address}, disconnecting user.")
        writer.close()
        await writer.wait_closed()
        if address in clients:
            del clients[address]
        if address in client_seq_nums:
            del client_seq_nums[address]
        if address in server_seq_nums:
            del server_seq_nums[address]
        if address in nack_retries:
            del nack_retries[address]
        print(f"Connection with {address} closed due to too many NACKs.")


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


async def kick_user(username):
    for address, user in clients.items():
        if user == username:
            writer = None
            for writer_key in rooms.values():
                for w in writer_key:
                    if w.get_extra_info("peername") == address:
                        writer = w
                        break
                if writer:
                    break
            if writer:
                await send_and_store_message(
                    writer,
                    MessageType.COMMAND,
                    "You have been kicked by the server",
                    client_seq_nums[address],
                )
                writer.close()
                await writer.wait_closed()
                if address in clients:
                    del clients[address]
                if address in client_seq_nums:
                    del client_seq_nums[address]
                if address in server_seq_nums:
                    del server_seq_nums[address]
                if address in nack_retries:
                    del nack_retries[address]
                print(f"User {username} kicked from the server.")
                return
    print(f"User {username} not found.")


async def main():
    server = await asyncio.start_server(handle_client, "0.0.0.0", 5555)
    print("Server listening on 0.0.0.0:5555")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
