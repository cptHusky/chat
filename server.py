import socket
from threading import Thread, active_count
from chat_lib import Message, Transport

CONNECTION_ERRORS = (
    ConnectionAbortedError,
    ConnectionResetError
)

HOST = '127.0.0.1'
PORT = 55555

class Server(Transport):
    def __init__(self, host, port):
        super().__init__(host, port)
        self.connections = []

    def handle_single_client(self, connection, address):
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
                for con in self.connections:
                    Transport.send(con, out_str)
                    print(con)

                print('[MSG_SEND] Sending end.')

            except CONNECTION_ERRORS:
                print(f'[CON_DISC] {inc_addr}:{inc_port} has disconnected.')
                self.connections.remove(connection)
                print(f'[CON_STAT] Active connections: {active_count() - 1}')
                break

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((self.host, self.port))
            sock.listen()
            print(f'[SRV_STAT] Server started at {self.host}:{self.port}')

            while True:
                connection, address = sock.accept()
                self.connections.append(connection)
                thread = Thread(target=self.handle_single_client, args=(connection, address))
                thread.start()
                print(f'[CON_STAT] Active connections: {active_count() - 1}')

if __name__ == '__main__':
    server = Server(HOST, PORT)
    server.start()
