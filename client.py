import socket
import threading
import time

def send_message(client_socket, username):
    while True:
        message = input("\nEnter message: ")
        # Construct the message with username and timestamp
        full_message = f"\n{username}: {message} ({time.strftime('%H:%M:%S')})"
        client_socket.send(full_message.encode())

def receive_message(client_socket):
    while True:
        data = client_socket.recv(1024).decode()
        print("\nReceived:", data)

def main():
    # Server configuration
    host = "127.0.0.1"
    port = 5555

    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    client_socket.connect((host, port))
    print("\nConnected to server")

    # Start a thread for receiving messages
    receive_thread = threading.Thread(target=receive_message, args=(client_socket,))
    receive_thread.start()

    # Wait for the server to request the username
    username = input("\nChoose a username: ")
    # Send the chosen username to the server
    client_socket.send(username.encode())

    # Start a thread for sending messages
    send_thread = threading.Thread(target=send_message, args=(client_socket, username))
    send_thread.start()

    # Wait for both threads to finish
    send_thread.join()
    receive_thread.join()

    # Close the connection
    client_socket.close()

if __name__ == "__main__":
    main()
