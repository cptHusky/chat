import pytest
from unittest.mock import MagicMock

from chat_lib import Message


def test_pack():
    message = Message(username='test_user', text='test_message')
    packed_message = message.pack()
    assert isinstance(packed_message, str)
    assert 'timestamp' in packed_message
    assert 'username' in packed_message
    assert 'text' in packed_message

def test_unpack():
    message = Message()
    packed_message = '{"timestamp": 1682899200000, "username": "test_user", "text": "test_message"}'
    unpacked_message = message.unpack(packed_message)
    assert isinstance(unpacked_message, dict)
    assert unpacked_message['timestamp'] == 1682899200000
    assert unpacked_message['username'] == 'test_user'
    assert unpacked_message['text'] == 'test_message'

def test_receive():
    mock_socket = MagicMock()
    mock_socket.recv.return_value = b'{"timestamp": 1682899200000, "username": "test_user", "text": "test_message"}'
    message = Message()
    received_message = message.receive(mock_socket)
    assert isinstance(received_message, dict)
    assert received_message['timestamp'] == 1682899200000
    assert received_message['username'] == 'test_user'
    assert received_message['text'] == 'test_message'
    mock_socket.recv.assert_called_once_with(1024)

def test_receive_empty_msg():
    mock_socket = MagicMock()
    mock_socket.recv.return_value = b''
    message = Message()
    with pytest.raises(ConnectionAbortedError):
        message.receive(mock_socket)

def test_send():
    mock_socket = MagicMock()
    message = Message(username='test_user', text='test_message')
    message.send(mock_socket)
    mock_socket.sendall.assert_called_once()
