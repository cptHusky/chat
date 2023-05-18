import asyncio
import aioconsole
import socket
from chat_lib import Message, AIOTransport


EXIT_TEXT = 'Disconnected from server, press ENTER to close.\n'
HOST = '127.0.0.1'
PORT = 55555
USERNAME = 'anon'

DISCONNECT_ERRORS = (ConnectionAbortedError, OSError)

class Client(AIOTransport):
    async def start(self):
        reader, writer = await asyncio.open_connection(HOST, PORT)
        receive_task = asyncio.create_task(self.receive_message(reader))
        send_task = asyncio.create_task(self.send_message(writer))
        await asyncio.gather(receive_task, send_task)


    async def send_message(self, connection: socket.socket) -> None:
        while True:
            out_text = await aioconsole.ainput('Input your message or type "quit":\n')
            if out_text == '':
                print('Can not send empty messages!')
                continue
            if out_text == 'quit':
                connection.close()
                raise SystemExit(0)

            out_str = Message(USERNAME, out_text).pack()
            await self.send_async(connection, out_str)
            print('Message sent!\n')


    async def receive_message(self, connection: socket.socket) -> None:
        while True:
            try:
                inc_str = await self.receive_async(connection)
            except DISCONNECT_ERRORS:
                break

            inc_msg = Message().unpack(inc_str)
            print(inc_msg)


if __name__ == '__main__':
    while True:
        USERNAME = input('Set username before connection:\n')
        if not USERNAME:
            continue
        else:
            break
    client = Client(HOST, PORT)
    asyncio.run(client.start())
