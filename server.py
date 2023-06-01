import asyncio
from chat_lib import Message, AIOTransport
from uuid import uuid4

CONNECTION_ERRORS = (
    ConnectionAbortedError,
    ConnectionResetError
)

HOST = '127.0.0.1'
PORT = 55555


class Server(AIOTransport):

    def __init__(self, host: str, port: int) -> None:
        super().__init__(host, port)
        self.connections: dict[uuid4.UUID, (asyncio.StreamWriter, bool, str)] = {}

    async def send_to_all_connections(self, msg: str) -> None:
        print(f'[MSG_SEND] Message ({msg}) is being sent to:')

        for connection_id in self.connections:

            if self.connections[connection_id][1]:
                await self.send_async(self.connections[connection_id][0], msg)
                client_host, client_port = self.connections[connection_id][0].get_extra_info('peername')
                print(f'| {connection_id} | {client_host}:{client_port} |')

    async def handle_single_client(
            self,
            reader: asyncio.streams.StreamReader,
            writer: asyncio.streams.StreamWriter
    ) -> None:

        connection_id = uuid4()
        self.connections[connection_id] = [writer, bool, str]
        self.connections[connection_id][1] = True
        number_active_connections = len([connection[1] for connection in self.connections.values() if connection[1]])

        host, port = writer.get_extra_info('peername')
        print(f'[CON_STAT] Connection accepted from: {host}:{port}, assigned ID:\n{connection_id}')
        print(f'[CON_STAT] Active connections: {number_active_connections}\nConnections list:')

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
                self.connections[connection_id][1] = False
                number_active_connections =\
                    len([connection[1] for connection in self.connections.values() if connection[1]])
                print(f'[CON_STAT] Active connections: {number_active_connections}')
                break

    async def start(self) -> None:
        server_instance = await asyncio.start_server(self.handle_single_client, self.host, self.port)
        print(f'[SRV_STAT] Server started at {self.host}:{self.port}')
        
        async with server_instance:
            await server_instance.serve_forever()


if __name__ == '__main__':
    server = Server(HOST, PORT)
    asyncio.run(server.start())
