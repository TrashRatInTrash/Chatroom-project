from scapy.all import *


def create_custom_packet(packet_type, content, timestamp):
    # Construct the custom payload
    custom_payload = f"{packet_type}:{content}:{timestamp}"
    print(f"custom packet structure:{custom_payload}")
    # Create a raw packet with the custom payload
    packet = Raw(load=custom_payload)

    return packet


def send_custom_packet(packet, iface=None):
    # Send the packet on the specified interface (default is None which means all interfaces)
    sendp(packet, iface=iface, verbose=0)


if __name__ == "__main__":
    import time

    # Example usage
    packet_type = "message"  # or "command"
    content = "Hello, World!"
    timestamp = time.time()

    # Create the custom packet
    packet = create_custom_packet(packet_type, content, timestamp)

    # Print the packet for verification
    print(packet.show())

    # Send the custom packet (specify the interface if needed, e.g., iface="eth0")
    send_custom_packet(packet)
