import socket
import threading
import time
import subprocess
import message_handler

# REF:
# Python official doc for socket lib
# https://docs.python.org/3/library/socket.html
# Python offical doc for threading lib
# https://docs.python.org/3/library/threading.html


# incomplete attempt to add a remote shell to the server for admin
def handle_command(command):
    try:
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        return result.decode()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.output.decode()}"


# function to handle client connections
# constantly listening to messages from clients and then broadcasts to all connected clientss
def handle_client(client_socket, address):
    print(f"\nAccepted connection from {address}")
    print(f"\n Current active threads {threading.active_count()}")
    client_socket.send("\nChoose a username: ".encode())

    username = client_socket.recv(1024).decode()
    print(f"\n{address} chose username: {username}")

    # Add username, IP, and port to the mapping dictionary
    user_map[username] = address

    try:
        while True:
            data = client_socket.recv(1024).decode()
            if not data:
                break

            # Parse message
            message_dict = message_handler.parse_message(data)
            
            # Check if it's a command
            if message_dict['type'] == "command":
                command_content = message_dict['content']
                if command_content == "qqq":
                    # Disconnect the client
                    print(f"\n{username} ({address}) disconnected gracefully.")
                    del user_map[username]  # Remove user from the mapping dictionary
                    break
            else:
                print(f"\nReceived from {username} ({address}): {message_dict['content']} received at {message_dict['time_sent']}")

                # Broadcast message string
                broadcast(data.encode())
    
    except Exception as e:
        print(f"Exception in thread {threading.current_thread().name} ({username}): {e}")
    finally:
        # close client socket and remove client socket

        client_socket.close()
        clients.remove(client_socket)



# Function to broadcast message to all clients in list
def broadcast(message):
    for client in clients:
        client.send(message)


def main():

    # Server configuration
    host = "127.0.0.1"
    port = 5555

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_socket.bind((host, port))

    server_socket.listen()

    print(f"\nServer listening on {host}:{port}")

    # constantly listening for client connections
    while True:
        client_socket, address = server_socket.accept()

        clients.append(client_socket)

        # Start a new thread to handle each client
        client_thread = threading.Thread(
            target=handle_client, args=(client_socket, address)
        )
        client_thread.start()


clients = []
user_map = {}

if __name__ == "__main__":
    main()
