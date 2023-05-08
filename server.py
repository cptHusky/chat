import socket
from threading import Thread, active_count
from chat_lib import Message, Transport

HOST = '127.0.0.1'
PORT = 55555

CONNECTION_ERRORS = (
    ConnectionAbortedError,
    ConnectionResetError
)

def handle_single_client(connection, address):
    inc_addr, inc_port = address
    print(f'Connection accepted from {inc_addr}:{inc_port}')

    try:
        inc_str = Transport.receive(connection)
        inc_msg = Message().unpack(inc_str)
        print(f'Message received:\n{inc_msg}')
    except CONNECTION_ERRORS:
        print(f'{inc_addr}:{inc_port} has disconnected.')

    username, text = inc_msg['username'], inc_msg['text']
    out_str = Message(username, text).pack()
    Transport.send(connection, out_str)
    
if __name__ == '__main__':
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, PORT))
        sock.listen()
        print(f'Server started at {HOST}:{PORT}')
        connections_list = []
        while True:
            connection, address = sock.accept()
            connections_list.append(connection)
            thread = Thread(target=handle_single_client, args=(connection, address))
            thread.start()
            print(f'Active connections: {active_count() - 1}')
