import asyncio
from chat_lib import Message, AIOTransport
import sqlite3

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

        # в счастливом будущем, где у клиента будет сообщение логина, 'Someone' станет {username}
        username, text = 'Server', 'Someone has entered the chat'
        await self.send_to_all_connections(Message(username, text).pack())

        while True:

            try:
                inc_str = await self.receive_async(reader)
                inc_msg = Message().unpack(inc_str)
                print(f'[MSG_RECV] Message received:\n{inc_msg}')

                username, text = inc_msg.username, inc_msg.text
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


if __name__ == '__main__':
    server = Server(HOST, PORT)
    asyncio.run(server.start())
