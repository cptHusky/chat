import asyncio
from chat_lib import Message, AIOTransport, Sec, Logger
from uuid import uuid4
import os
import sqlite3

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization

CONNECTION_ERRORS = (
    ConnectionAbortedError,
    ConnectionResetError
)

HOST = '127.0.0.1'
PORT = 55555


class Connection:
    def __init__(self):
        self.id: int = None
        self.user: str = None
        self.is_connected: bool = None
        # self.host: str = None
        # self.port: int = None
        self.public_key: bytes = None


class Server(AIOTransport):

    def __init__(self, host: str, port: int) -> None:
        super().__init__(host, port)
        self.writers: dict[int, asyncio.streams.StreamWriter] = {}

        self.db = sqlite3.connect('server.db')
        self.cursor = self.db.cursor()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS connections(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT,                              # буду наполнять после разработки сообщения логина
                is_connected BOOL,
                public_key BLOB                         # буду наполнять после разработки сообщения логина
            );
        ''')

        self.db.commit()

    async def start(self) -> None:
        current_directory = os.getcwd()
        filename = 'server.log'
        logfile = os.path.join(current_directory, filename)
        self.log = Logger(logfile)
        log_text = '---Server has started'
        self.log.write(log_text)
        self.private_key, self.public_key = Sec.generate_keys()
        log_text = 'Key generated'
        self.log.write(log_text)
        server_instance = await asyncio.start_server(self.handle_single_client, self.host, self.port)
        print(f'[SRV_STAT] Server started at {self.host}:{self.port}')

        async with server_instance:
            await server_instance.serve_forever()
        
    async def send_to_all_connections(self, msg: str) -> None:
        print(f'[MSG_SEND] Message ({msg}) is being sent to:')
        self.cursor.execute('''SELECT id FROM connections WHERE is_connected = True''')
        active_connections_id = self.cursor.fetchall()

        for connection_id in active_connections_id:
            connection_id = connection_id[0]
            connection = self.writers[connection_id]
            await self.send_async(connection, msg)
            client_host, client_port = connection.get_extra_info('peername')

            print(f'| {connection_id} | {client_host}:{client_port} |')

    async def handle_single_client(
            self,
            reader: asyncio.streams.StreamReader,
            writer: asyncio.streams.StreamWriter
    ) -> None:

      connection = Connection()
        self.cursor.execute('''SELECT MAX(id) FROM connections''')

        try:
            connection.id = self.cursor.fetchone()[0] + 1
        except TypeError:
            connection.id = 1

        self.writers[connection.id] = writer
        connection.is_connected = True

        self.cursor.execute(f'''
        INSERT INTO connections(is_connected) 
        VALUES ({connection.is_connected});
        ''')
        self.db.commit()

        host, port = writer.get_extra_info('peername')
        print(f'[CON_STAT] Connection accepted from: {host}:{port}, assigned ID:\n{connection.id}')
        print(f'[CON_STAT] Active connections: {self.get_number_active_connections()}\nConnections list:')
        log_text = f'Accepted connection from {host}:{port}, assigned ID: {connection.id}, connection info:\n{writer}'
        self.log.write(log_text)
        log_text = f'Connections currently active: {number_active_connections}'
        self.log.write(log_text)
        login_str = await self.receive_async(reader)
        log_text = f'Received login raw:\n{login_str}'
        self.log.write(log_text)
        login_msg = Message().unpack(login_str)
        log_text = f'Received message:\n{login_msg}'
        self.log.write(log_text)

        # в счастливом будущем, где у клиента будет сообщение логина, 'Someone' станет {username}
        username, text = 'Server', 'Someone has entered the chat'
        await self.send_to_all_connections(Message(username, text).pack())

        while True:

            try:
                inc_str = await self.receive_async(reader)
                print(f'[RAW_RECV]{inc_str}')
                log_text = f'Received raw:\n{inc_str}'
                self.log.write(log_text)
                inc_msg = Message().unpack(inc_str)
                log_text = f'Received message:\n{inc_msg}'
                self.log.write(log_text)
                print(f'[MSG_RECV] Message received:\n{inc_msg}')
                username, text, signature = inc_msg.username, inc_msg.text, inc_msg.signature

                if not self.client_verification(connection_id, signature, text):
                    self.connections[connection_id][1] = False
                    self.connections[connection_id][0].close()

                out_str = Message(username, text).pack()
                await self.send_to_all_connections(out_str)

                print('[MSG_SEND] Sending end.')

            except CONNECTION_ERRORS:
                self.cursor.execute(f'''
                UPDATE connections
                SET is_connected = False 
                WHERE id = {connection.id};
                ''')
                self.db.commit()

                print(f'[CON_STAT] Active connections: {self.get_number_active_connections()}')
                break

    def get_number_active_connections(self):
        self.cursor.execute('''
            SELECT SUM(CAST(is_connected AS INT))
            FROM connections
            WHERE is_connected = 1;
            ''')
        number_active_connections = self.cursor.fetchone()[0]
        if not number_active_connections:
            number_active_connections = 0
        return number_active_connections

    async def start(self) -> None:
        server_instance = await asyncio.start_server(self.handle_single_client, self.host, self.port)
        print(f'[SRV_STAT] Server started at {self.host}:{self.port}')

        async with server_instance:
            await server_instance.serve_forever()
            
            
    def client_verification(self, connection_id, signature: str, text):
        print(type(signature), '\nAAAAAAAAAAAAAAAAAAAAAAAAAAA')
        public_key = self.connections[connection_id][2]
        public_key_byted = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        public_key_str = public_key_byted.decode('latin1')
        print(f'{public_key_str=}')
        signature_byted = signature.encode('latin1')
        text_byted = text.encode()
        print(f'{public_key=}')
        try:
            public_key.verify(
                signature_byted,
                text_byted,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception as exp:
            print(exp)
            print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
            return False


if __name__ == '__main__':
    server = Server(HOST, PORT)
    asyncio.run(server.start())
