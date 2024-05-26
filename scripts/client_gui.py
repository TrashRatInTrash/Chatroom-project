import asyncio
import message_handler
from CONSTANTS import MessageType
import json
import threading
import tkinter as tk
from tkinter import scrolledtext

client_seq_num = 0
server_seq_num = 0
running = True
username_set = False
sent_packets = {}  # Store sent packets for potential retransmission

async def send_message(writer, msg_type, content):
    global client_seq_num
    packet = message_handler.create_message(msg_type, content, client_seq_num)
    sent_packets[client_seq_num] = packet  # Store the packet
    writer.write(bytes(packet))
    await writer.drain()
    client_seq_num += 1

async def receive_message(reader, message_display):
    global server_seq_num
    global running
    try:
        while running:
            packet = await message_handler.receive_message(reader, server_seq_num)
            if packet.seq_num != server_seq_num:
                await send_nack(writer, server_seq_num)
                continue
            server_seq_num += 1
            message_display.config(state=tk.NORMAL)
            message_display.insert(tk.END, f"Received: {packet.content}\n")
            message_display.config(state=tk.DISABLED)

            # Handle NACK message
            if packet.type == MessageTypeMapping[MessageType.NACK]:
                expected_seq_num = int(packet.content.split()[-1])
                if expected_seq_num in sent_packets:
                    await retransmit_packet(writer, sent_packets[expected_seq_num])
    except Exception as e:
        print(f"Error receiving message: {e}")

async def send_nack(writer, expected_seq_num):
    nack_message = message_handler.create_message(MessageType.NACK, f"NACK for {expected_seq_num}", expected_seq_num)
    writer.write(bytes(nack_message))
    await writer.drain()

async def retransmit_packet(writer, packet):
    writer.write(bytes(packet))
    await writer.drain()

def handle_user_input(writer, message_entry, message_display):
    global running
    global username_set
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def send_input():
        global username_set
        message = message_entry.get()
        message_entry.delete(0, tk.END)

        if not username_set:
            if message.startswith("/username"):
                loop.run_until_complete(
                    send_message(writer, MessageType.COMMAND, message)
                )
                username_set = True
            else:
                message_display.config(state=tk.NORMAL)
                message_display.insert(
                    tk.END,
                    "Please set your username first using /username <your_username>\n",
                )
                message_display.config(state=tk.DISABLED)
                return
        else:
            if message.startswith("/"):
                command = message.strip()
                if command == "/qqq":
                    loop.run_until_complete(
                        send_message(writer, MessageType.COMMAND, command)
                    )
                    running = False
                elif command.startswith("/create"):
                    loop.run_until_complete(
                        send_message(writer, MessageType.COMMAND, command)
                    )
                elif command.startswith("/join"):
                    loop.run_until_complete(
                        send_message(writer, MessageType.COMMAND, command)
                    )
                elif command.startswith("/leave"):
                    loop.run_until_complete(
                        send_message(writer, MessageType.COMMAND, command)
                    )
                elif command == "/wrong":
                    loop.run_until_complete(
                        send_message_with_incorrect_checksum(writer, MessageType.MESSAGE, "Test message with incorrect checksum")
                    )
                elif command == "/users":
                    loop.run_until_complete(
                        send_message(writer, MessageType.COMMAND, command)
                    )
                else:
                    message_display.config(state=tk.NORMAL)
                    message_display.insert(tk.END, "Unknown command\n")
                    message_display.config(state=tk.DISABLED)
            else:
                loop.run_until_complete(
                    send_message(writer, MessageType.MESSAGE, message)
                )

    return send_input

async def send_message_with_incorrect_checksum(writer, msg_type, content):
    global client_seq_num
    packet = message_handler.create_message(msg_type, content, client_seq_num)
    packet.checksum = b'incorrect_checksum'  # Intentionally set an incorrect checksum
    writer.write(bytes(packet))
    await writer.drain()
    client_seq_num += 1

async def start_network(reader, writer, message_display):
    await receive_message(reader, message_display)

def main():
    global running

    root = tk.Tk()
    root.title("Chat Client")

    message_display = scrolledtext.ScrolledText(
        root, state=tk.DISABLED, width=50, height=20
    )
    message_display.grid(row=0, column=0, padx=10, pady=10, columnspan=3)

    message_entry = tk.Entry(root, width=40)
    message_entry.grid(row=1, column=0, padx=10, pady=10)

    send_button = tk.Button(root, text="Send")
    send_button.grid(row=1, column=1, padx=10, pady=10)

    send_incorrect_button = tk.Button(root, text="Send Incorrect Checksum")
    send_incorrect_button.grid(row=2, column=1, padx=10, pady=10)

    close_button = tk.Button(
        root, text="Close", command=lambda: on_closing(writer, root)
    )
    close_button.grid(row=1, column=2, padx=10, pady=10)

    loop = asyncio.get_event_loop()
    reader, writer = loop.run_until_complete(asyncio.open_connection("192.168.28.83", 5555))
    print("Connected to server")

    send_input = handle_user_input(writer, message_entry, message_display)
    send_button.config(command=send_input)

    send_incorrect_input = handle_incorrect_checksum_input(writer, message_entry)
    send_incorrect_button.config(command=send_incorrect_input)

    network_thread = threading.Thread(
        target=loop.run_until_complete,
        args=(start_network(reader, writer, message_display),),
    )
    network_thread.start()

    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(writer, root))
    root.mainloop()

    running = False
    network_thread.join()

def on_closing(writer, root):
    global running
    running = False
    if writer:
        writer.close()
        asyncio.run(writer.wait_closed())
    root.destroy()

if __name__ == "__main__":
    main()
