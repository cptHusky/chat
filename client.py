import asyncio
import curses
import os
import sys
from chat_lib import Message, AIOTransport, Sec, Logger


from cryptography.hazmat.primitives import serialization

HOST = '127.0.0.1'
PORT = 55555

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

    def input_result_print(self, condition: str) -> None:
        self.send_window.clear()

        match condition:

            case 'success':
                self.send_window.addstr(3, 1, 'Message sent!')

            case 'empty':
                self.send_window.addstr(3, 1, 'Can not send empty messages!')

            case 'login_ok':
                self.send_window.addstr(3, 1, 'Logged in!')

            case _:
                self.send_window.addstr(3, 1, condition)

        self.send_window.border()
        self.send_window.refresh()


class Client(Interface, AIOTransport):

    async def start(self) -> None:
        current_directory = os.getcwd()
        filename = 'client.log'
        logfile = os.path.join(current_directory, filename)
        self.log = Logger(logfile)
        log_text = '---Client has started'
        self.log.write(log_text)
        self.private_key, self.public_key = Sec.generate_keys()
        log_text = 'Keys generated'
        self.log.write(log_text)
        self.init_interface()
        log_text = 'Interface started'
        self.log.write(log_text)
        reader, writer = await asyncio.open_connection(HOST, PORT)
        log_text = f'Connection established at the {HOST}:{PORT}, connection info:\n' \
                   f'{writer}'
        self.log.write(log_text)
        await self.send_login(writer)
        log_text = 'Login sent'
        self.log.write(log_text)

        try:
            receive_task = asyncio.create_task(self.receive_message(reader))
            send_task = asyncio.create_task(self.send_message(writer))
            await asyncio.gather(receive_task, send_task)
            log_text = 'Receive and sending coroutine has started'
            self.log.write(log_text)

        except SystemExit:
            log_text = 'Disconnected!'
            self.log.write(log_text)
            print('Disconnected!')            

    async def send_message(self, connection: asyncio.StreamWriter) -> None:
        while True:
            out_text = await asyncio.to_thread(self.input_message)
            log_text = f'Message entered: {out_text}'
            self.log.write(log_text)

            if out_text == '':
                self.input_result_print('empty')
                continue

            if out_text == 'quit':
                connection.close()

            out_str = Message(USERNAME, out_text, self.private_key).pack()
            log_text = f'Sending: {out_str}'
            self.log.write(log_text)
            await self.send_async(connection, out_str)
            log_text = 'Sent!'
            self.log.write(log_text)
            self.input_result_print('success')

    async def receive_message(self, connection: asyncio.StreamReader) -> None:
        while True:

            try:
                inc_str = await self.receive_async(connection)
                log_text = f'Received raw:\n{inc_str}'
                self.log.write(log_text)

            except DISCONNECT_ERRORS:
                log_text = 'Connection error, disconnecting.'
                self.log.write(log_text)
                break

            inc_msg = Message().unpack(inc_str)
            log_text = f'Received message:\n{inc_msg}'
            self.log.write(log_text)

            self.print_inc_msg_and_roll(str(inc_msg))

    async def send_login(self, connection: asyncio.StreamWriter):
        public_key_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        public_key_str = public_key_bytes.decode()
        login_str = Message(USERNAME, public_key_str, self.private_key).pack()
        await self.send_async(connection, login_str)
        log_text = f'Login message sent raw:\n{login_str}'
        self.log.write(log_text)
        self.input_result_print('login_ok')


if __name__ == '__main__':
    while True:

        USERNAME = input('Set username before connection:\n')

        if not USERNAME:
            continue

        else:
            break

    client = Client(HOST, PORT)
    asyncio.run(client.start())
