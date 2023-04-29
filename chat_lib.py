import json
import time

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
    
    def unpack(self, msg: str) -> dict:
        parsed_msg = json.loads(msg)
        return parsed_msg
    
    def receive(self, sock):
        inc_msg_byte = sock.recv(1024)
        if  inc_msg_byte == b'':
            raise ConnectionAbortedError
#? Взял ошибку из уже хэндлящихся, не искал правильную
        inc_msg_pack = inc_msg_byte.decode()
        inc_msg = self.unpack(inc_msg_pack)
        return inc_msg
    
    def send(self, sock):
        out_msg_pack = self.pack()
        out_msg_byte = out_msg_pack.encode()
        sock.sendall(out_msg_byte)