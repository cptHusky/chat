import pytest
from chat_lib import Transport, Message

def test_transport_send():
    class MockSocket:
        def sendall(self, msg):
            assert msg.encode() == b'Hello, world!'

    transport = Transport()
    transport.send = MockSocket().sendall
    transport.send('Hello, world!')


def test_transport_receive():
    class MockSocket:
        def recv(self, length):
            assert length == 1024
            return b'Received message'

    transport = Transport()
    transport.recv = MockSocket().recv
    received_msg = transport.receive()
    assert received_msg == 'Received message'


def test_message_pack():
    message = Message(username='John', text='Hello, world!')
    packed_msg = message.pack()


def test_message_unpack():
    packed_msg = '{"timestamp": 123456789, "username": "John", "text": "Hello, world!"}'
    parsed_msg = Message.unpack(packed_msg)


if __name__ == '__main__':
    pytest.main()
