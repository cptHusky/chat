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
    
    def receive():
        ...

    def send(self):
        ...