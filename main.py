import asyncio
import gui
import logging
import sys
import time

import configparser

from tkinter import messagebox

from connection_handler import ConnectionHandler
from reciever import Reciever, save_queue_to_file
from sender import Sender, WrongHash
from startup_window import show_startup_window


logger = logging.getLogger('chat')


def main():
    show_startup_window()
    logger.setLevel(logging.DEBUG)
    file_logger = logging.FileHandler('debug_log.txt', encoding='UTF-8')
    file_logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    file_logger.setFormatter(formatter)
    logger.addHandler(file_logger)

    config = configparser.ConfigParser()
    config.read('config.ini')

    loop = asyncio.get_event_loop()

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    history_queue = asyncio.Queue()

    sender = Sender(
        config['CONNECTION']['host'],
        config['CONNECTION']['send_port'],
        config['CONNECTION']['nickname'],
        config['CONNECTION'].get('key'),
        send_queue=sending_queue,
    )
    reciever = Reciever(
        config['CONNECTION']['host'],
        config['CONNECTION']['read_port'],
        messages_queue,
        history_queue,
    )
    handler = ConnectionHandler(sender, reciever, status_updates_queue)
    with open('logs.txt', 'r') as file:
        for line in file.readlines():
            messages_queue.put_nowait(line)

    async def launch_messenger():
        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(gui.draw(messages_queue, sending_queue, status_updates_queue))
                tg.create_task(save_queue_to_file(history_queue))
                tg.create_task(handler.handle_connection())
        except Exception as ex_group:
            if ex_group.subgroup(gui.TkAppClosed):
                raise
            elif ex_group.subgroup(WrongHash):
                messagebox.showerror('Неверный токен', 'Укажите корректный токен в файле конфигурации или удалите его для повторной регистрации')
        finally:
            async with asyncio.TaskGroup() as tg2:
                tg2.create_task(sender.cleanup())
                tg2.create_task(reciever.cleanup())

    try:
        loop.run_until_complete(launch_messenger())
    except KeyboardInterrupt:
        sys.exit(0)
    finally:
        config['CONNECTION']['key'] = sender.token
        with open('config.ini', 'w') as configfile:
            config.write(configfile)


if __name__ == '__main__':
        main()
