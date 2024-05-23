import socket
import threading
import message_handler
import json

client_seq_num = 0  # Sequence number for sending messages
server_seq_num = 0  # Sequence number for receiving messages


def send_incorrect_checksum_message(sock, content):
    global client_seq_num
    valid_message = message_handler.create_message("message", content, client_seq_num)
    message_dict = json.loads(valid_message)
    message_dict["checksum"] = "incorrectchecksum"
    incorrect_message = json.dumps(message_dict)
    sock.sendall(incorrect_message.encode())
    client_seq_num += 1


def handle_command(sock, command):
    global client_seq_num
    if command == "/qqq":
        message_handler.send_message(sock, "command", "qqq", client_seq_num)
        client_seq_num += 1
        return False
    elif command == "/wrong":
        send_incorrect_checksum_message(
            sock, "This is a test message with incorrect checksum."
        )
    else:
        print("Unknown command")
    return True


def send_messages(sock):
    global client_seq_num
    username = input("Choose a username: ")
    message_handler.send_message(sock, "response", username, client_seq_num)
    client_seq_num += 1

    while True:
        message = input("\nEnter message: ")
        if message.startswith("/"):
            if not handle_command(sock, message):
                break
        else:
            message_handler.send_message(sock, "message", message, client_seq_num)
            client_seq_num += 1


def receive_messages(sock):
    global server_seq_num
    while True:
        try:
            message = message_handler.receive_message(sock, server_seq_num)
            if not message:
                break
            if message:
                print(f"\nReceived: {message['content']} at {message['time_sent']}")
                server_seq_num += 1
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
