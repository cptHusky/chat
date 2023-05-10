from abc import ABC, abstractmethod
import json
import time
import socket


class Protocol(ABC):
    @abstractmethod
    def send(self: socket, msg) -> None:
        pass

    @abstractmethod
    def receive(self: socket) -> str:
        pass


class Transport(Protocol):
    def send(self: socket, msg: str) -> None:
        msg_to_send = msg.encode()
        self.sendall(msg_to_send)

    def receive(self: socket) -> str:
        inc_msg_byte = self.recv(1024)
        if inc_msg_byte == b'':
            raise ConnectionAbortedError
        
        inc_msg = inc_msg_byte.decode()
        return inc_msg


class Message:
    def __init__(self, username: str = None, text: str = None):
        self.text = text
        self.username = username

    def pack(self) -> str:
        json_msg = json.dumps({
            "timestamp": int(time.time() * 1000),
            "username": self.username,
            "text": self.text,
        })
        return json_msg

    @staticmethod
    def unpack(msg: str) -> dict:
        parsed_msg = json.loads(msg)
        return parsed_msg
