import socket
import threading
import message_handler
from CONSTANTS import MessageType

clients = {}
client_seq_nums = {}
server_seq_nums = {}
rooms = {}


def return_command_code(command):
    if command["content"] == "qqq":
        return 1
    if command["content"].startswith("/create"):
        return 5
    if command["content"].startswith("/join"):
        return 6


def handle_client(client_socket, address):
    print(f"\nAccepted connection from {address}")
    print(f"\nCurrent active threads: {threading.active_count()}")

    client_seq_nums[client_socket] = 0
    server_seq_nums[client_socket] = 0

    message_handler.send_message(
        client_socket,
        MessageType.INFO,
        "Choose a username:",
        client_seq_nums[client_socket],
    )
    client_seq_nums[client_socket] += 1

    current_room = None

    try:
        message = message_handler.receive_message(
            client_socket, server_seq_nums[client_socket]
        )
        if message:
            if message["seq_num"] != server_seq_nums[client_socket]:
                raise ValueError("Sequence number mismatch")
            server_seq_nums[client_socket] += 1
            if message["type"] == MessageType.RESP.value:
                username = message["content"].strip()
            else:
                raise ValueError("Invalid username response")
        else:
            raise ValueError("No message received for username")

        print(f"\n{address} chose username: {username}")
        clients[client_socket] = username

        while True:
            try:
                message = message_handler.receive_message(
                    client_socket, server_seq_nums[client_socket]
                )
                if not message:
                    break

                if message["seq_num"] != server_seq_nums[client_socket]:
                    raise ValueError("Sequence number mismatch")

                server_seq_nums[client_socket] += 1

                if message["type"] == MessageType.COMMAND.value:
                    command_content = message["content"].strip()

                    code = return_command_code(message)

                    print(f"\nCommand code {code}")
                    if code == 1:
                        message_handler.send_message(
                            client_socket,
                            MessageType.RESP,
                            1,
                            client_seq_nums[client_socket],
                        )
                        client_seq_nums[client_socket] += 1
                        break
                    elif code == 5:
                        room_id = f"room_{len(rooms) + 1}"
                        rooms[room_id] = [client_socket]
                        current_room = room_id
                        message_handler.send_message(
                            client_socket,
                            MessageType.RESP,
                            f"Created and joined room {room_id}",
                            client_seq_nums[client_socket],
                        )
                        client_seq_nums[client_socket] += 1
                    elif code == 6:
                        _, room_id = command_content.split()
                        if room_id in rooms:
                            rooms[room_id].append(client_socket)
                            current_room = room_id
                            message_handler.send_message(
                                client_socket,
                                MessageType.RESP,
                                f"Joined room {room_id}",
                                client_seq_nums[client_socket],
                            )
                            client_seq_nums[client_socket] += 1
                        else:
                            message_handler.send_message(
                                client_socket,
                                MessageType.RESP,
                                "Room does not exist",
                                client_seq_nums[client_socket],
                            )
                            client_seq_nums[client_socket] += 1

                else:
                    if current_room:
                        print(
                            f"\nReceived from {username} ({address}) in room {current_room}: {message['content']} received at {message['time_sent']}"
                        )
                        message_handler.send_message(
                            client_socket,
                            MessageType.RESP,
                            0,
                            client_seq_nums[client_socket],
                        )
                        broadcast(message["content"], username, current_room)

                        client_seq_nums[client_socket] += 1
                    else:
                        message_handler.send_message(
                            client_socket,
                            MessageType.RESP,
                            "You are not in a room. Use /create or /join to enter a room.",
                            client_seq_nums[client_socket],
                        )
                        client_seq_nums[client_socket] += 1

            except ValueError as ve:
                print(f"Value Error: {ve}")
                nack_message_str = message_handler.create_message(
                    MessageType.NACK, str(ve), server_seq_nums[client_socket] - 1
                )
                client_socket.sendall(nack_message_str.encode())
            except Exception as e:
                print(f"Exception in handling client: {e}")
                nack_message_str = message_handler.create_message(
                    MessageType.NACK, str(e), server_seq_nums[client_socket] - 1
                )
                client_socket.sendall(nack_message_str.encode())

    except Exception as e:
        print(f"Exception in thread {threading.current_thread().name} ({address}): {e}")
        message_handler.send_message(
            client_socket, MessageType.RESP, 4, client_seq_nums[client_socket]
        )
        client_seq_nums[client_socket] += 1
    finally:
        if current_room and client_socket in rooms.get(current_room, []):
            rooms[current_room].remove(client_socket)
        client_socket.close()
        if client_socket in clients:
            del clients[client_socket]
        if client_socket in client_seq_nums:
            del client_seq_nums[client_socket]
        if client_socket in server_seq_nums:
            del server_seq_nums[client_socket]
        print(f"Connection with {address} closed.")


def broadcast(content, username, room_id):
    for client in rooms.get(room_id, []):
        try:
            message_handler.send_message(
                client,
                MessageType.MESSAGE,
                f"{username}: {content}",
                client_seq_nums[client],
            )
            client_seq_nums[client] += 1
        except Exception as e:
            print(f"Failed to send message to {clients[client]}: {e}")


def main():
    host = "127.0.0.1"
    port = 5555

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen()

    print(f"\nServer listening on {host}:{port}")

    try:
        while True:
            client_socket, address = server_socket.accept()
            client_thread = threading.Thread(
                target=handle_client, args=(client_socket, address)
            )
            client_thread.start()
    except KeyboardInterrupt:
        print("\nServer shutting down.")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()
