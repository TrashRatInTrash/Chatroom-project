import socket
import threading
import message_handler

clients = {}
client_seq_nums = {}  # Sequence numbers for sending messages to clients
server_seq_nums = {}  # Sequence numbers for receiving messages from clients


def return_command_code(command):
    if command["content"] == "qqq":
        return 1


def handle_client(client_socket, address):
    print(f"\nAccepted connection from {address}")
    print(f"\nCurrent active threads: {threading.active_count()}")

    # Initialize sequence numbers for the client
    client_seq_nums[client_socket] = 0
    server_seq_nums[client_socket] = 0

    message_handler.send_message(
        client_socket, "info", "Choose a username:", client_seq_nums[client_socket]
    )
    client_seq_nums[client_socket] += 1

    message = message_handler.receive_message(
        client_socket, server_seq_nums[client_socket]
    )
    server_seq_nums[client_socket] += 1
    if message and message["type"] == "response":
        username = message["content"].strip()
    else:
        raise ValueError("Invalid username response")

    print(f"\n{address} chose username: {username}")
    clients[client_socket] = username

    try:
        while True:
            message = message_handler.receive_message(
                client_socket, server_seq_nums[client_socket]
            )
            if not message:
                break

            server_seq_nums[client_socket] += 1

            if message["type"] == "command":
                code = return_command_code(message)
                print(f"\n command code {code}")
                if code == 1:
                    message_handler.send_message(
                        client_socket,
                        "rsp",
                        1,
                        client_seq_nums[client_socket],  # command success
                    )
                    client_seq_nums[client_socket] += 1
                    break
            else:
                print(
                    f"\nReceived from {username} ({address}): {message['content']} received at {message['time_sent']}"
                )
                broadcast(message["content"], username)
                message_handler.send_message(
                    client_socket,
                    "rsp",
                    0,
                    client_seq_nums[client_socket],  # message success
                )
                client_seq_nums[client_socket] += 1
    except ValueError as ve:
        print(f" Value Error: {ve}, user disconnected")
        message_handler.send_message(
            client_socket,
            "rsp",
            2,
            client_seq_nums[client_socket],  # checksum catchall error
        )
        client_seq_nums[client_socket] += 1
    except Exception as e:
        print(
            f"Exception in thread {threading.current_thread().name} ({username}): {e}"
        )
        message_handler.send_message(
            client_socket,
            "rsp",
            4,
            client_seq_nums[client_socket],  # default catchall error
        )
        client_seq_nums[client_socket] += 1
    finally:
        client_socket.close()
        del clients[client_socket]
        del client_seq_nums[client_socket]
        del server_seq_nums[client_socket]
        print(f"Connection with {username} ({address}) closed.")


def broadcast(content, username):
    for client in clients:
        message_handler.send_message(
            client, "message", content, client_seq_nums[client]
        )
        client_seq_nums[client] += 1


def main():
    host = "127.0.0.1"
    port = 5555

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen()

    print(f"\nServer listening on {host}:{port}")

    while True:
        client_socket, address = server_socket.accept()
        client_thread = threading.Thread(
            target=handle_client, args=(client_socket, address)
        )
        client_thread.start()


if __name__ == "__main__":
    main()
