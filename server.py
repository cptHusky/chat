import asyncio
from chat_lib import Message, AIOTransport, Sec, Logger
import sqlite3

import os

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
        self.id: int | None = None
        self.user: str | None = None
        self.is_connected: bool | None = None
        self.host: str | None = None
        self.port: int | None = None
        self.public_key = None


class Server(AIOTransport):

    def __init__(self, host: str, port: int) -> None:
        super().__init__(host, port)
        self.writers: dict[int, asyncio.streams.StreamWriter] = {}

        self.db = sqlite3.connect('server.db')
        self.cursor = self.db.cursor()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS connections(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT,
                is_connected BOOL,
                host TEXT,
                port INTEGER,
                public_key BLOB
            );
        ''')

        self.db.commit()

        self.cursor.execute('''UPDATE connections SET is_connected = FALSE''')
        self.db.commit()

    async def start(self) -> None:
        current_directory = os.getcwd()
        filename = 'server.log'
        logfile = os.path.join(current_directory, filename)
        self.log = Logger(logfile)
        log_text = '[APP_STAT] Server has started'
        self.log.write(log_text)
        self.private_key, self.public_key = Sec.generate_keys()
        log_text = '[KEY_GENE] Key generated'
        self.log.write(log_text)
        server_instance = await asyncio.start_server(self.handle_single_client, self.host, self.port)
        print(f'[APP_STAT] Server started at {self.host}:{self.port}')

        async with server_instance:
            await server_instance.serve_forever()

    async def send_to_all_connections(self, msg: str) -> None:
        print(f'[MSG_SEND] Message ({msg}) is being sent to:')
        log_text = f'[MSG_SEND] Sending raw:\n{msg}\nTo:'
        self.log.write(log_text)
        self.cursor.execute('''SELECT id FROM connections WHERE is_connected = True''')
        active_connections_id = self.cursor.fetchall()

        for connection_id_tuple in active_connections_id:
            connection_id = connection_id_tuple[0]
            connection = self.writers[connection_id]
            await self.send_async(connection, msg)
            client_host, client_port = connection.get_extra_info('peername')

            log_text = f'| {connection_id} | {client_host}:{client_port} |'
            self.log.write(log_text)
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

        connection.is_connected = True
        self.cursor.execute(f'''
        INSERT INTO connections(is_connected) 
        VALUES ({connection.is_connected});
        ''')
        self.db.commit()
        self.writers[connection.id] = writer

        connection.host, connection.port = writer.get_extra_info('peername')
        self.update_field_by_id(self.db, 'connections', 'host', connection.id, connection.host)
        self.update_field_by_id(self.db, 'connections', 'port', connection.id, connection.port)

        login_str = await self.receive_async(reader)
        log_text = f'[LOG_RECV] Received login raw:\n{login_str}'
        print(f'[LOG_RECV] {login_str}')
        self.log.write(log_text)
        login_msg = Message().unpack(login_str)

        public_key_byted = login_msg.text.encode()
        self.update_field_by_id(self.db, 'connections', 'public_key', connection.id, public_key_byted)
        connection.public_key = serialization.load_pem_public_key(public_key_byted)

        connection.user = login_msg.username
        self.update_field_by_id(self.db, 'connections', 'user', connection.id, connection.user)

        print(f'[CON_STAT] Connection accepted from {connection.host}:{connection.port}, assigned ID: {connection.id}')
        print(f'[CON_STAT] Active connections: {self.get_number_active_connections()}')

        if not self.client_verification(connection, login_msg.username, login_msg.signature, login_msg.text):
            connection.is_connected = False
            self.update_field_by_id(self.db, 'connections', 'is_connected', connection.id, False)
            self.writers[connection.id].close()

        text = f'{connection.user} has entered the chat'
        await self.send_to_all_connections(Message('Server', text).pack())

        log_text = f'[CON_STAT] Connection accepted from {connection.host}:{connection.port}, ' \
                   f'assigned ID: {connection.id}, connection info:\n{writer}'
        self.log.write(log_text)

        log_text = f'[CON_STAT] Connections currently active: {self.get_number_active_connections()}'
        self.log.write(log_text)

        while True:

            try:
                inc_str = await self.receive_async(reader)
                log_text = f'[MSG_RECV] Received raw:\n{inc_str}'
                self.log.write(log_text)
                inc_msg = Message().unpack(inc_str)
                log_text = f'[MSG_RECV] Received message:\n{inc_msg}\n'
                self.log.write(log_text)
                print(log_text)

                username, text, signature = inc_msg.username, inc_msg.text, inc_msg.signature

                if not self.client_verification(connection, username, signature, text):
                    log_text = f'[USR_STAT] Did not validate user: {connection.user}, connection id: {connection.id}'
                    self.log.write(log_text)
                    print(log_text)
                    connection.is_connected = False
                    self.update_field_by_id(self.db, 'connections', 'is_connected', connection.id, False)
                    self.writers[connection.id].close()
                    log_text = f'[CON_STAT] Disconnected connection id: {connection.id}'
                    self.log.write(log_text)
                    print(log_text)

                out_str = Message(username, text).pack()
                await self.send_to_all_connections(out_str)
                print('[MSG_SEND] Sending end.')

            except CONNECTION_ERRORS:
                log_text = f'[CON_STAT] Error with connection id: {connection.id}'
                self.log.write(log_text)
                connection.is_connected = False
                self.update_field_by_id(self.db, 'connections', 'is_connected', connection.id, False)
                log_text = f'[CON_STAT] Disconnected connection id: {connection.id}'
                self.log.write(log_text)
                break

    def update_field_by_id(self, db, table: str, column: str, entry_id: int, value: any) -> bool:
        cursor = db.cursor()
        query = f'''
            UPDATE {table}
            SET {column} = ? 
            WHERE id = {entry_id};
            '''

        try:
            cursor.execute(query, (value,))
            self.db.commit()
            return True

        except Exception as exp:
            log_text = f'......update failed......\n{query}\n------\n{exp}\n^^^^^^update failed^^^^^^'
            self.log.write(log_text)
            print(log_text)
            return False
        # можно добавить в будущем при использовании проверку

    def select_field_by_id(self, db, table: str, column: str, entry_id: int) -> any:
        cursor = db.cursor()
        cursor.execute(f'''
        SELECT {column}
        FROM {table}
        WHERE id = {entry_id};
        ''')
        result = cursor.fetchone()[0]
        return result

    def client_verification(self, connection: Connection, username: str, signature: str, text: str):
        if not username == connection.user:
            log_text = f'[USR_VLDT] Wrong user at connection id {connection.id}. {username} != {connection.user}'
            self.log.write(log_text)
            print(log_text)
            return False

        signature_byted = signature.encode('latin1')
        text_byted = text.encode()
        try:
            connection.public_key.verify(
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
            log_text = f'[USR_VLDT] Exception caught:\n{exp}'
            self.log.write(log_text)
            print(log_text)
            log_text = f'[USR_VLDT] Signature not verified for connection id {connection.id}, check above'
            self.log.write(log_text)
            print(log_text)
            return False

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


if __name__ == '__main__':
    server = Server(HOST, PORT)
    asyncio.run(server.start())
