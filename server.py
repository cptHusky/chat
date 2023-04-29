import socket
from chat_lib import Message

HOST = '127.0.0.1'
PORT = 55555

CONNECTION_ERRORS = (
    ConnectionAbortedError,
    ConnectionResetError
)


if __name__ == '__main__':
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((HOST, PORT))
        sock.listen()
        print(f'Server started at {HOST}:{PORT}')

        connection, address = sock.accept()
        inc_addr, inc_port = address

        with connection:
            print(f'Connection accepted from {inc_addr}:{inc_port}')

            while True:
                try:
                    inc_msg = Message().receive(connection)
                except CONNECTION_ERRORS:
                    print(f'{inc_addr}:{inc_port} has disconnected.')
                    break
                print(f'Message received:\n{inc_msg}')

                username, text = inc_msg['username'], inc_msg['text']
                out_msg = Message(username, text)
                out_msg.send(connection)
