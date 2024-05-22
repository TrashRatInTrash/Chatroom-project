import socket
import threading
import time
import message_handler
import json

# REF:
# Python official doc for socket lib
# https://docs.python.org/3/library/socket.html
# Python offical doc for threading lib
# https://docs.python.org/3/library/threading.html

#test

def send_incorrect_checksum_message(socket, content):
    # Create a valid message first
    valid_message = message_handler.create_message("message", content)
    message_dict = json.loads(valid_message)
    # Change the checksum to an incorrect one
    message_dict["checksum"] = "incorrectchecksum"
    incorrect_message = json.dumps(message_dict)
    socket.sendall(incorrect_message.encode())


# Message sent is currently in the form of
# {username} {text message} {user timestamp}
def handle_command(client_socket, command):
    if command == "/qqq":
        message_handler.send_message(client_socket, "command", "qqq")
        return False
    elif command == "/wrong":
        send_incorrect_checksum_message(
            client_socket, "This is a test message with incorrect checksum."
        )
    else:
        print("Unknown command")
    return True


def send_messages(client_socket):
    username = input("Choose a username: ")
    message_handler.send_message(client_socket, "response", username)

    while True:
        message = input("\nEnter message: ")
        if message.startswith("/"):
            if not handle_command(client_socket, message):
                break
        else:
            message_handler.send_message(client_socket, "message", message)


def receive_messages(client_socket):
    while True:
        try:
            message = message_handler.receive_message(client_socket)
            if not message:
                break
            if message:
                print(f"\nReceived: {message['content']} at {message['time_sent']}")
            else:
                print("\nReceived invalid data")
        except OSError:
            print("Connection closed by the server.")
            break


def main():
    host = "127.0.0.1"
    port = 5555

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    print("\nConnected to server")

    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    receive_thread.start()

    send_thread = threading.Thread(target=send_messages, args=(client_socket,))
    send_thread.start()

    send_thread.join()
    client_socket.close()
    print("Disconnected from server")


if __name__ == "__main__":
    main()
