import socket
import threading

# Function to handle client connections
def handle_client(client_socket, address):
    print(f"Accepted connection from {address}")
    while True:
        # Receive data from the client
        data = client_socket.recv(1024).decode()
        if not data:
            break
        print(f"Received from {address}: {data}")
        # Broadcast the received message to all clients
        broadcast(data.encode())
    client_socket.close()

# Function to broadcast message to all clients
def broadcast(message):
    for client in clients:
        client.send(message)

# Main server function
def main():
    # Server configuration
    host = "127.0.0.1"
    port = 5555

    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the host and port
    server_socket.bind((host, port))

    # Listen for incoming connections
    server_socket.listen()

    print(f"Server listening on {host}:{port}")

    while True:
        # Accept incoming connections
        client_socket, address = server_socket.accept()

        # Add the new client to the list of clients
        clients.append(client_socket)

        # Start a new thread to handle the client
        client_thread = threading.Thread(target=handle_client, args=(client_socket, address))
        client_thread.start()

# List to store connected clients
clients = []

if __name__ == "__main__":
    main()
