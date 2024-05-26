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


address = "127.0.0.1"
port = 5555