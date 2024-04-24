import socket
import threading

def send_message(client_socket):
    while True:
        message = input("Enter message: ")
        client_socket.send(message.encode())

def receive_message(client_socket):
    while True:
        data = client_socket.recv(1024).decode()
        print("Received from server:", data)

def main():
    # Server configuration
    host = "127.0.0.1"
    port = 5555

    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    client_socket.connect((host, port))
    print("Connected to server")

    # Start a thread for sending messages
    send_thread = threading.Thread(target=send_message, args=(client_socket,))
    send_thread.start()

    # Start a thread for receiving messages
    receive_thread = threading.Thread(target=receive_message, args=(client_socket,))
    receive_thread.start()

    # Wait for both threads to finish
    send_thread.join()
    receive_thread.join()

    # Close the connection
    client_socket.close()

if __name__ == "__main__":
    main()
