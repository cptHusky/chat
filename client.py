import socket
from threading import Thread
from chat_lib import Message, Transport

EXIT_TEXT = 'Disconnected from server, press ENTER to close.\n'
HOST = '127.0.0.1'
PORT = 55555
USERNAME = 'anon'

DISCONNECT_ERRORS = (ConnectionAbortedError, OSError)

class Client():
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
            connection.connect((HOST, PORT))
            print(f'Connected to {HOST}:{PORT}')
            print(connection)
            send_thread = Thread(target=self.send_message, args=(connection, ))
            recv_thread = Thread(target=self.receive_message, args=(connection, ))
            send_thread.start()
            recv_thread.start()
            send_thread.join()
            recv_thread.join()

    def output(self, msg: dict) -> None:
        print('Message received:')
        for key, value in msg.items():
            match key:
                case 'timestamp':
                    print(f'Time sent: {value}')
                case 'username':
                    print(f'Sender: {value}')
                case 'text':
                    print(f'Message:\n{value}')
                case _:
                    print(f'{key}: {value}')
        print()


    def send_message(self, connection: socket.socket) -> None:
        while True:
            out_text = input('Input your message or type "quit":\n')
            if out_text == 'quit':
                connection.close()
                raise SystemExit(0)

            out_str = Message(USERNAME, out_text).pack()
            Transport.send(connection, out_str)
            print('Message sent!\n')


    def receive_message(self, connection: socket.socket) -> None:
        while True:
            try:
                inc_str = Transport.receive(connection)
            except DISCONNECT_ERRORS:
                break

            inc_msg = Message().unpack(inc_str)
            self.output(inc_msg)


if __name__ == '__main__':
    USERNAME = input('Set username before connection:\n')

    client = Client(HOST, PORT)
    client.start()
    
    input(EXIT_TEXT)
