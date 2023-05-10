# test_chat_lib.py
import pytest
from chat_lib import Transport, Message

# Test Transport class
def test_transport_send():
    # Create a mock socket object
    class MockSocket:
        def sendall(self, msg):
            assert msg.encode() == b'Hello, world!'

    transport = Transport()
    transport.send = MockSocket().sendall
    transport.send('Hello, world!')


def test_transport_receive():
    # Create a mock socket object
    class MockSocket:
        def recv(self, length):
            assert length == 1024
            return b'Received message'

    transport = Transport()
    transport.recv = MockSocket().recv
    received_msg = transport.receive()
    assert received_msg == 'Received message'


# Test Message class
def test_message_pack():
    message = Message(username='John', text='Hello, world!')
    packed_msg = message.pack()
    # Add assertions to check the contents of the packed message


def test_message_unpack():
    packed_msg = '{"timestamp": 123456789, "username": "John", "text": "Hello, world!"}'
    parsed_msg = Message.unpack(packed_msg)
    # Add assertions to check the parsed message


# Run the tests
if __name__ == '__main__':
    pytest.main()
