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
    def __init__(self, host, port):
        super().__init__(host, port)
        self.connections: dict[int, asyncio.StreamWriter | None] = {}

    async def send_to_all_connections(self, msg: str):
        print(f'[MSG_SEND] Message ({msg}) is being sent to:')
        for id in self.connections:
            if self.connections[id] is not None:
                await self.send_async(self.connections[id], msg)
                client_host, client_port = self.connections[id].get_extra_info('peername')
                print(f'| {id} | {client_host}:{client_port} |')       

    async def handle_single_client(self, reader, writer):
        connection_id = uuid4()
        self.connections[connection_id] = writer
        number_active_connections = len([value for value in self.connections.values() if value is not None])
        host, port = writer.get_extra_info('peername')
        print(f'[CON_STAT] Connection accepted from: {host}:{port}, assigned ID:\n{connection_id}')
        print(f'[CON_STAT] Active connections: {number_active_connections}\nConnections list:')
        username, text = 'Server', 'Someone has entered the chat'
# в счастливом будущем, где у клиента будет сообщение логина, 'Someone' станет {username}
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
                self.connections[connection_id] = None
                number_active_connections = len([value for value in self.connections.values() if value is not None])
                print(f'[CON_STAT] Active connections: {number_active_connections}')
                break


    async def start(self):
        server = await asyncio.start_server(self.handle_single_client, self.host, self.port)
        print(f'[SRV_STAT] Server started at {self.host}:{self.port}')
        
        async with server:
            await server.serve_forever()


if __name__ == '__main__':
    server = Server(HOST, PORT)
    asyncio.run(server.start())
