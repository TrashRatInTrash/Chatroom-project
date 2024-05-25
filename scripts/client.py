import asyncio
import message_handler
from CONSTANTS import MessageType
import json
import threading

client_seq_num = 0
server_seq_num = 0
running = True

async def send_message(writer, msg_type, content):
    global client_seq_num
    await message_handler.send_message(writer, msg_type, content, client_seq_num)
    client_seq_num += 1

async def receive_message(reader):
    global server_seq_num
    global running
    try:
        while running:
            message = await message_handler.receive_message(reader, server_seq_num)
            server_seq_num += 1
            print(f"Received message: {message["content"]}")  # Debugging statement
    except Exception as e:
        print(f"Error receiving message: {e}")

def handle_user_input(writer):
    global running
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while running:
        message = input("Enter message: ")
        if message.startswith("/"):
            command = message.strip()
            if command == "/qqq":
                loop.run_until_complete(send_message(writer, MessageType.COMMAND, command))
                running = False
                break
            elif command.startswith("/create"):
                loop.run_until_complete(send_message(writer, MessageType.COMMAND, command))
            elif command.startswith("/join"):
                loop.run_until_complete(send_message(writer, MessageType.COMMAND, command))
            elif command.startswith("/leave"):
                loop.run_until_complete(send_message(writer, MessageType.COMMAND, command))
            elif command == "/wrong":
                loop.run_until_complete(send_message(writer, MessageType.COMMAND, command))
            else:
                print("Unknown command")
        else:
            loop.run_until_complete(send_message(writer, MessageType.MESSAGE, message))

async def main():
    global running
    reader, writer = await asyncio.open_connection("127.0.0.1", 5555)
    print("Connected to server")

    input_thread = threading.Thread(target=handle_user_input, args=(writer,))
    input_thread.start()

    await receive_message(reader)

    print("Closing connection")
    writer.close()
    await writer.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
