import aiofiles
import asyncio
import datetime
import time

import configargparse

from gui import ReadConnectionStateChanged


class Reader:
    def __init__(self, host, port, *queues):
        self.host = host
        self.port = port
        self.writer = None
        self.reader = None
        self.queues = queues
        self.watchdog_queue = None

    async def start_connection(self, watchdog_queue):
        self.watchdog_queue = watchdog_queue
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

    async def read_to_queues(self):
        while True:
            message = await self.reader.read(1000)
            self.watchdog_queue.put_nowait(f"[{int(time.time())}] Connection is alive. New message in chat")
            text_line = f"[{datetime.datetime.now().strftime('%d.%m.%y %H:%M')}] {message.decode('UTF-8')}"
            for queue in self.queues:
                queue.put_nowait(text_line)

    async def cleanup(self):
        self.writer.close()
        await self.writer.wait_closed()


async def save_queue_to_file(queue, path='logs.txt'):
    while True:
        line = await queue.get()
        async with aiofiles.open(path, 'a') as file:
            await file.write(line)


async def main():
    argparser = configargparse.ArgParser(default_config_files=['config.ini'])
    argparser.add('-H', '--host', required=True, help='host')
    argparser.add('-p', '--recieve_port', required=True, help='port to recieve messages')
    argparser.add('-l', '--logs', required=True, help='log file name')
    args, _ = argparser.parse_known_args()
    reader = Reader(args.host, int(args.recieve_port))
    await reader.start_connection()
    async with aiofiles.open(args.logs, 'a') as file:
        await reader.read_to_file(file)


if __name__ == '__main__':
    asyncio.run(main())
