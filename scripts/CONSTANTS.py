from enum import Enum

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#       DO NOT TOUCH
#
#       use these and
#       dont add more
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class MessageType(Enum):
    COMMAND = "command"
    MESSAGE = "message"
    ACK = "ack"
    NACK = "nack"
    RESP = "resp"
    INFO = "info"
    HEARTBEAT = "heartbeat"

# 192.168.28.83
address = "127.0.0.1"
port = 5555