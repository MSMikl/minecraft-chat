import asyncio
import json
import logging

import configargparse

from reader import get_connection

logger = logging.getLogger('sender')


class WrongHash(Exception):
    pass


async def send_message(writer, message):
    text = " ".join(message)
    writer.write(text.encode('UTF-8'))
    writer.write('\n\n'.encode('UTF-8'))
    logger.debug(f"sent {text}")
    await writer.drain()


async def register(reader, writer, name):
    writer.write('\n'.encode('UTF-8'))
    await writer.drain()
    answer = await reader.read(1000)
    logger.debug(f"recieved {answer.decode('UTF-8')}")
    writer.write(fr"{name}".encode('UTF-8'))
    writer.write('\n'.encode('UTF-8'))
    logger.debug(f"sent {name}")
    await writer.drain()
    await reader.readline()
    answer = await reader.readline()
    logger.debug(f"recieved {answer.decode('UTF-8')}")
    user_data = json.loads(answer)
    if not user_data:
        raise WrongHash('Неизвестный токен. Проверьте его или зарегистрируйтесь заново')
    key = user_data['account_hash']
    return key


async def authenticate(reader, writer, key):
    writer.write(key.encode('UTF-8'))
    logger.debug(f"sent {key}")
    writer.write('\n'.encode('UTF-8'))
    await writer.drain()
    answer = await reader.readline()
    logger.debug(f"recieved {answer.decode('UTF-8')}")
    user_data = json.loads(answer)
    key = user_data['account_hash']
    return key


async def main():
    logger.setLevel(logging.DEBUG)
    file_logger = logging.FileHandler('debug_log.txt', encoding='UTF-8')
    file_logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    file_logger.setFormatter(formatter)
    logger.addHandler(file_logger)
    argparser = configargparse.ArgParser(default_config_files=['config.ini'])
    argparser.add('-H', '--host', required=True, help='host')
    argparser.add('-p', '--send_port', required=True, help='port to send messages')
    argparser.add('-k,', '--key', help="user's account hash")
    argparser.add('-n', help="user's nickname")
    argparser.add('message', nargs='*', help='Текст сообщения', default='')
    args, _ = argparser.parse_known_args()
    async with get_connection(args.host, args.send_port) as connection:
        reader, writer = connection
        answer = await reader.readline()
        logger.debug(f"recieved {answer.decode('UTF-8')}")
        if args.n:
            key = await register(reader, writer, args.n)
        else:
            key = await authenticate(reader, writer, args.key)
        args.key = key
        argparser.write_config_file(args, ['config.ini'])

        await send_message(writer, args.message)


if __name__ == '__main__':
    asyncio.run(main())
