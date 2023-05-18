from abc import ABC, abstractmethod
import asyncio
import datetime
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
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def send(self, connection: socket, msg: str) -> None:
        msg_to_send = msg.encode()
        connection.sendall(msg_to_send)

    def receive(self, connection: socket) -> str:
        inc_msg_byte = connection.recv(1024)
        if inc_msg_byte == b'':
            raise ConnectionAbortedError
        
        inc_msg = inc_msg_byte.decode()
        return inc_msg

class AIOTransport(Transport):
    async def send_async(self, connection: asyncio.StreamWriter, msg: str) -> None:
        msg_to_send = msg.encode()
        connection.write(msg_to_send)
        await connection.drain()

    async def receive_async(self, connection: asyncio.StreamReader) -> str:
        inc_msg_byte = await connection.read(1024)
        if inc_msg_byte == b'':
            raise ConnectionAbortedError
        
        inc_msg = inc_msg_byte.decode()
        return inc_msg

class Message:
    def __init__(self, username: str = None, text: str = None):
        self.text = text
        self.username = username
        self.timestamp = None

    def __str__(self):
        no_format_time = datetime.datetime.fromtimestamp(self.timestamp)
        human_time = no_format_time.strftime('%Y-%m-%d %H:%M:%S')
        bold_username = ''.join(('\033[1m', self.username, '\033[0m'))
# воспользовался решением через ANSI, не работает в cmd под win10, в терминале питона жирнеет
        to_print = f'[{human_time}]{bold_username}:{self.text}'
        return to_print

    def pack(self) -> str:
        json_msg = json.dumps({
            "timestamp": int(time.time()),
            "username": self.username,
            "text": self.text,
        })
        return json_msg

    @staticmethod
    def unpack(msg: str) -> 'Message':
        parsed_msg_dict = json.loads(msg)
        parsed_msg = Message(parsed_msg_dict['username'], parsed_msg_dict['text'])
        parsed_msg.timestamp = parsed_msg_dict['timestamp']
        return parsed_msg
