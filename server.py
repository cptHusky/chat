import asyncio
from chat_lib import Message, AIOTransport

CONNECTION_ERRORS = (
    ConnectionAbortedError,
    ConnectionResetError
)

HOST = '127.0.0.1'
PORT = 55555


class Server(AIOTransport):
    def __init__(self, host, port):
        super().__init__(host, port)
        self.connections = {}


    async def handle_single_client(self, reader, writer):
        connection_id = len(self.connections)
        self.connections[connection_id] = writer
        number_active_connections = len([value for value in self.connections.values() if value is not None])
        print(f'[CON_STAT] Active connections: {number_active_connections}\nConnections list:')
        for id in self.connections:
            if self.connections[id] is not None:
                client_host, client_port = self.connections[id].get_extra_info('peername')
                print(f'ID: {id:3} {client_host:20}:{client_port}')

        while True:
            try:
                inc_str = await self.receive_async(reader)
                inc_msg = Message().unpack(inc_str)
                print(f'[MSG_RECV] Message received:\n{inc_msg}')

                username, text = inc_msg.username, inc_msg.text
                out_str = Message(username, text).pack()

                print(f'[MSG_SEND] Message ({out_str}) is being sent to IDs:')
                for id in self.connections:
                    if self.connections[id] is not None:
                        await self.send_async(self.connections[id], out_str)
                        print(f'{id}, ', end='')
                print()

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
