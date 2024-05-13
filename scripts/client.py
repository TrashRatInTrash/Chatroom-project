import socket
import threading
import time
import message_handler

# REF:
# Python official doc for socket lib
# https://docs.python.org/3/library/socket.html
# Python offical doc for threading lib
# https://docs.python.org/3/library/threading.html


# Message sent is currently in the form of
# {username} {text message} {user timestamp}
def send_message(client_socket):
    while True:
        message = input("\nEnter message: ")
        if message == "/qqq":  # disconnect from server
            disconnect_command = message_handler.create_message("command", "qqq")
            client_socket.send(disconnect_command.encode())
            break
        else:  # create text message
            message_str = message_handler.create_message("message", message)
            client_socket.send(message_str.encode())


def receive_message(client_socket):
    while True:
        try:
            data = client_socket.recv(1024).decode()
            if not data:
                break
            # Check if data is non-empty and starts with '{' (indicating JSON format)
            if data and data.startswith("{"):
                message_dict = message_handler.parse_message(data)
                print(
                    "\nReceived:",
                    message_dict["content"],
                    "at",
                    message_dict["time_sent"],
                )
            else:
                print("\nReceived invalid data:", data)
        except OSError as e:
            # Handle OSError, which occurs when the socket is closed
            print("Connection closed by the server.")
            break


def main():
    # Server configuration
    host = "127.0.0.1"
    port = 5555

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client_socket.connect((host, port))
    print("\nConnected to server")

    # Start a thread for receiving messages
    receive_thread = threading.Thread(target=receive_message, args=(client_socket,))
    receive_thread.start()

    # Wait for the server to request the username
    username = input()
    # Send the chosen username to the server
    client_socket.send(username.encode())

    # Start a thread for sending messages
    send_thread = threading.Thread(target=send_message, args=(client_socket,))
    send_thread.start()

    # Main loop to wait until the send_thread terminates
    send_thread.join()

    # After breaking from the send_thread, close the connection and exit the program
    client_socket.close()
    print("Disconnected from server")


if __name__ == "__main__":
    main()
