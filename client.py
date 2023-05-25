import asyncio
import aioconsole
import curses
import socket
import sys
from chat_lib import Message, AIOTransport


EXIT_TEXT = 'Disconnected from server, press ENTER to close.\n'
HOST = '127.0.0.1'
PORT = 55555
USERNAME = 'anon'

DISCONNECT_ERRORS = (ConnectionAbortedError, OSError)

class Interface:
    def create_windows(self):
        stdscr = curses.initscr()
        curses.echo()
        stdscr.nodelay(True)
        self.heigth, self.length = stdscr.getmaxyx()
        self.send_window_height = 6
        self.receive_window_heigth = self.heigth - self.send_window_height
        self.receive_window = curses.newwin(self.receive_window_heigth, self.length, 0, 0)
        self.send_window = curses.newwin(self.send_window_height , self.length, self.receive_window_heigth, 0)
        self.receive_window.border()
        self.send_window.border()


class Client(Interface, AIOTransport):
    async def start(self):
        self.create_windows()
        reader, writer = await asyncio.open_connection(HOST, PORT)
        receive_task = asyncio.create_task(self.receive_message(reader))
        try:
            send_task = asyncio.create_task(self.send_message(writer))
            await asyncio.gather(receive_task, send_task)
        except SystemExit:
            print('Disconnected!')            


    async def send_message(self, connection: socket.socket) -> None:
        while True:
            out_text = await asyncio.to_thread(self.input_message)
            if out_text == '':
                self.send_window.addstr(3, 1, 'Can not send empty messages!')
                continue
            if out_text == 'quit':
                connection.close()

            out_str = Message(USERNAME, out_text).pack()
            await self.send_async(connection, out_str)
            self.send_window.clear()
            self.send_window.border()
            self.send_window.addstr(3, 1, 'Message sent!')

    def input_message(self):
        self.send_window.addstr(1, 1, 'Input your message or type "quit":')
        # text = await asyncio.to_thread(self.send_window.getstr)
        text = self.send_window.getstr(2, 1)
        return str(text)[2:-1]


    async def receive_message(self, connection: socket.socket) -> None:
        while True:
            try:
                inc_str = await self.receive_async(connection)
            except DISCONNECT_ERRORS:
                break

            inc_msg = Message().unpack(inc_str)
            self.receive_window.clear()
            self.receive_window.border()
            self.receive_window.addstr(1, 1, str(inc_msg))
            self.receive_window.refresh()


if __name__ == '__main__':
    while True:
        USERNAME = input('Set username before connection:\n')
        if not USERNAME:
            continue
        else:
            break
    client = Client(HOST, PORT)
    asyncio.run(client.start())
