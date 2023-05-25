import asyncio
import curses
from chat_lib import Message, AIOTransport

import locale

# Установка локали и кодировки
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')


EXIT_TEXT = 'Disconnected from server, press ENTER to close.\n'
HOST = '127.0.0.1'
PORT = 55555
USERNAME = 'anon'

DISCONNECT_ERRORS = (ConnectionAbortedError, OSError)


class Interface:

    def init_interface(self) -> None:
        stdscr = curses.initscr()
        curses.echo()
        curses.raw()
        stdscr.nodelay(True)

        self.heigth, self.length = stdscr.getmaxyx()
        self.send_window_height = 6
        self.receive_window_heigth = self.heigth - self.send_window_height

        self.greet_bar = curses.newwin(1, self.length, 0, 0)
        self.receive_window = curses.newwin(self.receive_window_heigth, self.length, 1, 0)
        self.send_window = curses.newwin(self.send_window_height, self.length, self.receive_window_heigth, 0)

        self.receive_window.border()
        self.send_window.border()

        self.messages_list = []

        self.greet_bar.addstr(f'Welcome back, {USERNAME}. Again.')

        self.greet_bar.refresh()
        self.receive_window.refresh()
        self.send_window.refresh()

    def print_inc_msg_and_roll(self, text: str) -> None:
        self.receive_window.clear()

        self.messages_list.append(text)

        lines_available_to_print = self.receive_window_heigth - 2
        messages_to_print = self.messages_list[0 - lines_available_to_print:][::0 - 1]

        for i, message in enumerate(messages_to_print):
            line = self.receive_window_heigth - i - 2
            self.receive_window.addstr(line, 1, message)

        self.receive_window.border()
        self.receive_window.refresh()

        self.send_window.move(2, 1)
        self.send_window.refresh()

    def input_message(self) -> str:
        self.send_window.addstr(1, 1, 'Input your message or type "quit":')
        text = self.send_window.getstr(2, 1)
        return str(text)[2:-1]

    def input_decor(self):
        ...


class Client(Interface, AIOTransport):

    async def start(self) -> None:
        self.init_interface()

        reader, writer = await asyncio.open_connection(HOST, PORT)

        try:
            receive_task = asyncio.create_task(self.receive_message(reader))
            send_task = asyncio.create_task(self.send_message(writer))
            await asyncio.gather(receive_task, send_task)

        except SystemExit:
            print('Disconnected!')            

    async def send_message(self, connection: asyncio.StreamWriter) -> None:
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

    async def receive_message(self, connection: asyncio.StreamReader) -> None:
        while True:

            try:
                inc_str = await self.receive_async(connection)

            except DISCONNECT_ERRORS:
                break

            inc_msg = Message().unpack(inc_str)

            self.print_inc_msg_and_roll(str(inc_msg))


if __name__ == '__main__':
    while True:

        USERNAME = input('Set username before connection:\n')

        if not USERNAME:
            continue

        else:
            break

    client = Client(HOST, PORT)
    asyncio.run(client.start())
