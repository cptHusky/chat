import socket

HOST = ''
PORT = 55555

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen()
    print(f'Server started at {HOST}:{PORT}')
    connection, address = sock.accept()
    print(type(connection))
    print(f'{connection=}')
    inc_addr, inc_port = address
    with connection:
        print(f'Connection accepted from {inc_addr}:{inc_port}')

        while True:
            try:
                data = connection.recvfrom(1024)
            except ConnectionAbortedError:
                print(f'{inc_addr}:{inc_port} has disconnected.')
                break
            message = data[0].decode()
            print('2')
            print(f'Message received:\n{message}')
            print('3')
            connection.sendall(message.encode())
            print('4')

                
        # sock.connect((HOST.PORT))
        # while True:
        #     msg = input('Input your message or type "quit":\n')
        #     if msg == 'quit':
        #         break
        #     sock.sendall(msg)
        #     data = sock.recv()
        #     print(f'Message received:{data}')
