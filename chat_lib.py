from abc import ABC, abstractmethod
import asyncio
import json
import time
import socket
import os
import datetime

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa


class Protocol(ABC):

    @abstractmethod
    def send(self, connection: socket, msg: str) -> None:
        pass

    @abstractmethod
    def receive(self, connection: socket) -> str:
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
        inc_msg_byte = await connection.read(2048)
        if inc_msg_byte == b'':
            raise ConnectionAbortedError
        inc_msg = inc_msg_byte.decode()
        return inc_msg


class Sec:
    @staticmethod
    def generate_keys():
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()

        return private_key, public_key


class Message:
    def __init__(self, username: str = None, text: str = None, private_key=None) -> None:
        self.text = text
        self.username = username
        self.timestamp = None
        if private_key:
            self.signature: str = self.get_signature(text, private_key)

    def __str__(self) -> str:
        no_format_time = datetime.datetime.fromtimestamp(self.timestamp)
        human_time = no_format_time.strftime('%Y-%m-%d %H:%M:%S')
        to_print = f'[{human_time}] {self.username} sent: {self.text}'
        return to_print

    def pack(self) -> str:
        try:
            json_msg = json.dumps({
                "timestamp": int(time.time()),
                "username": self.username,
                "text": self.text,
                "signature": self.signature,
            })
        except AttributeError:
            json_msg = json.dumps({
                "timestamp": int(time.time()),
                "username": self.username,
                "text": self.text,
                "signature": 'Server',
            })
        return json_msg

    def get_signature(self, text, private_key) -> str:
        text_byted = text.encode()
        print(f'{text_byted=}')
        signature = private_key.sign(
            text_byted,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        print(f'Signature {type(signature)}: {signature}\n')
        signature_str = signature.decode('latin1')
        return signature_str

    @staticmethod
    def unpack(msg: str) -> 'Message':
        parsed_msg_dict = json.loads(msg)
        parsed_msg = Message()
        parsed_msg.text = parsed_msg_dict['text']
        parsed_msg.username = parsed_msg_dict['username']
        parsed_msg.timestamp = parsed_msg_dict['timestamp']
        parsed_msg.signature = parsed_msg_dict['signature']
        return parsed_msg


class Logger:
    def __init__(self, file):
        self.file = file

    def write(self, log):
        event_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        max_file_size = 128 * 1024 * 1024  # 128 mb in bytes
        if os.path.exists(self.file) and os.path.getsize(self.file) > max_file_size:
            file_name, file_extension = os.path.splitext(self.file)
            file_number = 1
            while os.path.exists(f"{file_name}_{file_number}{file_extension}"):
                file_number += 1
            new_file = f"{file_name}_{file_number}{file_extension}"
            self.file = new_file

        with open(self.file, 'a', encoding='utf-8') as f:
            # print(f'{log=}\n{type(log)=}')
            f.write(f'[{event_time}] {log}\n')