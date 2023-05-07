import socket
from chat_lib import Message, Transport

HOST = '127.0.0.1'
PORT = 55555
USERNAME = 'cptHusky'


def output(msg: dict) -> None:
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


if __name__ == '__main__':
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
        connection.connect((HOST, PORT))
        print(f'Connected to {HOST}:{PORT}')

        while True:
            out_text = input('Input your message or type "quit":\n')
            if out_text == 'quit':
                break
            
            out_str = Message(USERNAME, out_text).pack()
            Transport.send(connection, out_str)
            print('Message sent!\n')

            inc_str = Transport.receive(connection)
            inc_msg = Message().unpack(inc_str)
            output(inc_msg)
