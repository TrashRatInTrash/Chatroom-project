from enum import Enum


class MessageType(Enum):
    COMMAND = "command"
    MESSAGE = "message"
    ACK = "ack"
    RESP = "resp"
    INFO = "info"
