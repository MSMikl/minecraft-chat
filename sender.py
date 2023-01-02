import asyncio
import json
import logging
import time


logger = logging.getLogger('chat')


class WrongHash(Exception):
    pass


class Sender:
    def __init__(self, host, port, name='Default', token=None, send_queue=None):
        self.host = host
        self.port = port
        self.name = name
        self.nickname = None
        self.token = token
        self.reader = None
        self.writer = None
        self.send_queue = send_queue
        self.watchdog_queue = None

    async def cleanup(self):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()

    async def start_connection(self, watchdog_queue):
        self.watchdog_queue = watchdog_queue
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        if self.token:
            await self.authenticate()
        else:
            await self.register()
  
    async def send_empty_lines(self, num_lines=1):
        text = ('\n' * num_lines)
        self.writer.write(text.encode('UTF-8'))       
        await self.writer.drain()
        logger.debug(f"sent{text}")

    async def send_message(self, message):
        text = " ".join(message)
        self.writer.write(text.encode('UTF-8'))
        self.watchdog_queue.put_nowait(f"[{int(time.time())}] Connection is alive. Message sent")
        await self.send_empty_lines(2)

    async def register(self):
        await self.send_empty_lines()
        answer = await self.reader.read(1000)
        self.watchdog_queue.put_nowait(f"[{int(time.time())}] Connection is alive. Promt before auth")
        logger.debug(f"recieved {answer.decode('UTF-8')}")
        self.writer.write(fr"{self.name}".encode('UTF-8'))
        await self.send_empty_lines()
        self.watchdog_queue.put_nowait(f"[{int(time.time())}] Connection is alive. Name sent")
        logger.debug(f"sent {self.name}")
        await self.reader.readline()
        answer = await self.reader.readline()
        self.watchdog_queue.put_nowait(f"[{int(time.time())}] Connection is alive. Registration done")
        logger.debug(f"recieved {answer.decode('UTF-8')}")
        user_data = json.loads(answer)
        self.token = user_data['account_hash']
        self.nickname = user_data['nickname']

    async def authenticate(self):
        await self.reader.readline()
        self.watchdog_queue.put_nowait(f"[{int(time.time())}] Connection is alive. Promt before auth")
        self.writer.write(self.token.encode('UTF-8'))
        await self.send_empty_lines()
        logger.debug(f"sent {self.token}")
        answer = await self.reader.readline()
        self.watchdog_queue.put_nowait(f"[{int(time.time())}] Connection is alive. Authorization done")
        logger.debug(f"recieved {answer.decode('UTF-8')}")
        user_data = json.loads(answer)
        if not user_data:
            raise WrongHash('Неизвестный токен. Проверьте его или зарегистрируйтесь заново')
        self.token = user_data['account_hash']
        self.nickname = user_data['nickname']

    async def send_from_queue(self):
        while True:
            message = await self.send_queue.get()
            await self.send_message(message)
