import socket
import threading
import time

# REF: 
# Python official doc for socket lib
# https://docs.python.org/3/library/socket.html
# Python offical doc for threading lib
# https://docs.python.org/3/library/threading.html

# Message sent is currently in the form of 
# {username} {text message} {user timestamp}
def send_message(client_socket, username):
    while True:
        message = input("\nEnter message: ")
        full_message = f"\n{username}: {message} ({time.strftime('%H:%M:%S')})"
        client_socket.send(full_message.encode())

# print out recieved message from server
def receive_message(client_socket):
    while True:
        data = client_socket.recv(1024).decode()
        print("\nReceived:", data)

def main():

    # Server configuration
    host = "127.0.0.1"
    port = 5555

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client_socket.connect((host, port))
    print("\nConnected to server")

    # start a thread for receiving messages
    receive_thread = threading.Thread(target=receive_message, args=(client_socket,))
    receive_thread.start()

    # wait for the server to request the username
    username = input("\nChoose a username: ")
    # send the chosen username to the server
    client_socket.send(username.encode())

    # start a thread for sending messages
    send_thread = threading.Thread(target=send_message, args=(client_socket, username))
    send_thread.start()

    send_thread.join()
    receive_thread.join()

    # Close the connection
    client_socket.close()

if __name__ == "__main__":
    main()
