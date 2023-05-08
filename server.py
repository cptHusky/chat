import socket
from threading import Thread, active_count
from chat_lib import Message, Transport

HOST = '127.0.0.1'
PORT = 55555

CONNECTION_ERRORS = (
    ConnectionAbortedError,
    ConnectionResetError
)
CONNECTIONS_LIST = []

def handle_single_client(connection, address):
    inc_addr, inc_port = address
    print(f'[CON_ACPT] Connection accepted from {inc_addr}:{inc_port}')

    while connection:
        try:
            inc_str = Transport.receive(connection)
            inc_msg = Message().unpack(inc_str)
            print(f'[MSG_RECV] Message received:\n{inc_msg}')

            username, text = inc_msg['username'], inc_msg['text']
            out_str = Message(username, text).pack()

            print(f'[MSG_SEND] Message ({out_str}) is being sent to:')
            for con in CONNECTIONS_LIST:
                Transport.send(con, out_str)
                print(con)

            print('[MSG_SEND] Sending end.')
            
        except CONNECTION_ERRORS:
            print(f'[CON_DISC] {inc_addr}:{inc_port} has disconnected.')
            CONNECTIONS_LIST.remove(connection)
            print(f'[CON_STAT] Active connections: {active_count() - 1}')
            break


if __name__ == '__main__':
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, PORT))
        sock.listen()
        print(f'[SRV_STAT] Server started at {HOST}:{PORT}')

        while True:
            connection, address = sock.accept()
            CONNECTIONS_LIST.append(connection)
            thread = Thread(target=handle_single_client, args=(connection, address))
            thread.start()
            print(f'[CON_STAT] Active connections: {active_count() - 1}')
