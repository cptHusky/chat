import socket

HOST = 'localhost'
PORT = 55555

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect((HOST, PORT))
    print(f'Connected to {HOST}:{PORT}')

    while True:
        msg = input('Input your message or type "quit":\n')
        if msg == 'quit':
            break
        sock.sendall(msg.encode())

        
        data = sock.recv(1024)
        message = data.decode()
        print(f'Message received:\n{message}')


