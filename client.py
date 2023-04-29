import socket
from chat_lib import Message

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
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((HOST, PORT))
        print(f'Connected to {HOST}:{PORT}')

        while True:
            text = input('Input your message or type "quit":\n')
            if text == 'quit':
                break
            
            out_msg = Message(USERNAME, text)
            out_msg_pack = out_msg.pack()
            out_msg_byte = out_msg_pack.encode()
            sock.sendall(out_msg_byte)
            print('Message sent!\n')

            inc_msg_byte = sock.recv(1024)
            inc_msg_pack = inc_msg_byte.decode()
            inc_msg = Message().unpack(inc_msg_pack)
            output(inc_msg)
