import socket
import threading
import subprocess
import message_handler


def handle_command(command):
    try:
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        return result.decode()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.output.decode()}"


def handle_client(client_socket, address):
    print(f"\nAccepted connection from {address}")
    print(f"\nCurrent active threads: {threading.active_count()}")

    message_handler.send_message(client_socket, "info", "Choose a usEername:")
    message = message_handler.receive_message(client_socket)
    if message and message["type"] == "response":
        username = message["content"].strip()
    else:
        raise ValueError("Invalid username response")

    print(f"\n{address} chose username: {username}")
    user_map[client_socket] = username
    clients.append(client_socket)

    try:
        while True:
            message = message_handler.receive_message(client_socket)
            if not message:
                break

            if message["type"] == "command" and message["content"] == "qqq":
                print(f"\n{username} ({address}) disconnected gracefully.")
                break
            else:
                print(
                    f"\nReceived from {username} ({address}): {message['content']} received at {message['time_sent']}"
                )
                broadcast(message["content"], username)

    except Exception as e:
        print(
            f"Exception in thread {threading.current_thread().name} ({username}): {e}"
        )
    finally:
        client_socket.close()
        clients.remove(client_socket)
        if client_socket in user_map:
            del user_map[client_socket]
        print(f"Connection with {username} ({address}) closed.")


def broadcast(content, username):
    message_str = message_handler.create_message("message", f"{username}: {content}")
    for client in clients:
        client.sendall(message_str.encode())


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


clients = []
user_map = {}

if __name__ == "__main__":
    main()
