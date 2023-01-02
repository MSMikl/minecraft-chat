import asyncio
import logging
import socket
import time

from contextlib import asynccontextmanager

import gui


async def ping_connection(writer, reader, logger):
    while True:
        writer.write('\n'.encode('UTF-8'))
        try:
            async with asyncio.timeout(3):
                await writer.drain()
                await reader.readline()
        except TimeoutError:
            logger.debug(f"[{int(time.time())}] No connection. Trying to reconnect")
            raise ConnectionError
        await asyncio.sleep(3)


async def handle_watchdog_queue(queue, logger):
    timeouts = 0
    while True:
        try:
            async with asyncio.timeout(2):
                message = await queue.get()
                logger.debug(message)
                timeouts = 0
        except TimeoutError:
            logger.debug(f"[{int(time.time())}] 2s timeout is expired")
            timeouts += 1
            if timeouts > 3:
                logger.debug(f"[{int(time.time())}] No new messages. Trying to reconnect")
                raise ConnectionError


async def watch_for_connection(writer, reader, watchdog_queue):
    watchdog_logger = logging.getLogger('watchdog')
    async with asyncio.TaskGroup() as tg:
        tg.create_task(ping_connection(writer, reader, watchdog_logger))
        tg.create_task(handle_watchdog_queue(watchdog_queue, watchdog_logger))


class ConnectionHandler:
    def __init__(self, sender, reciever, status_queue):
        self.sender = sender
        self.reciever = reciever
        self.status_queue = status_queue
        self.watchdog_queue = asyncio.Queue()
        self.logger = logging.getLogger('watchdog')
        self.logger.setLevel(logging.DEBUG)
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(stream_handler)
    
    @asynccontextmanager
    async def establish_connection(self):
        try:
            self.status_queue.put_nowait(gui.SendingConnectionStateChanged('устанавливаем соединение'))
            self.status_queue.put_nowait(gui.ReadConnectionStateChanged('устанавливаем соединение'))
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.reciever.start_connection(self.watchdog_queue))
                tg.create_task(self.sender.start_connection(self.watchdog_queue))
            self.status_queue.put_nowait(gui.SendingConnectionStateChanged('соединение установлено'))
            self.status_queue.put_nowait(gui.ReadConnectionStateChanged('соединение установлено'))
            self.status_queue.put_nowait(gui.NicknameReceived(self.sender.nickname))
            yield
        finally:
            await self.reciever.cleanup()
            await self.sender.cleanup()

    async def handle_connection(self):
        while True:
            try:
                async with self.establish_connection():
                    try:
                        async with asyncio.TaskGroup() as tg:
                            send_task = tg.create_task(self.sender.send_from_queue())
                            read_task = tg.create_task(self.reciever.read_to_queues())
                            watchdog = tg.create_task(watch_for_connection(self.sender.writer, self.sender.reader, self.watchdog_queue))
                    except* ConnectionError:
                        send_task.cancel()
                        read_task.cancel()
            except ExceptionGroup as ex_group:
                if ex_group.subgroup(socket.gaierror):
                    await asyncio.sleep(3)
                    continue
