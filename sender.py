import asyncio
import json
import logging

import configargparse


logger = logging.getLogger('sender')


class WrongHash(Exception):
    pass

async def get_sender_connection(host, port, name='Default', key=None):
    reader, writer = await asyncio.open_connection(host, port)
    answer = await reader.readline()
    logger.debug(f"recieved {answer.decode('UTF-8')}")
    print(answer.decode('UTF-8'))
    if not key:
        writer.write('\n'.encode('UTF-8'))
        await writer.drain()
        answer = await reader.read(1000)
        logger.debug(f"recieved {answer.decode('UTF-8')}")
        print(answer.decode('UTF-8'))
        writer.write(name.encode('UTF-8'))
        writer.write('\n'.encode('UTF-8'))
        logger.debug(f"sent {name}")
        await writer.drain()
        await reader.readline()
    else:
        writer.write(key.encode('UTF-8'))
        logger.debug(f"sent {key}")
        writer.write('\n'.encode('UTF-8'))
        await writer.drain()
    answer = await reader.readline()
    print(answer.decode('UTF-8'))
    logger.debug(f"recieved {answer.decode('UTF-8')}")
    user_data = json.loads(answer)
    if not user_data:
        raise WrongHash
    nickname = user_data['nickname']
    key = user_data['account_hash']
    return writer, nickname, key


async def main():
    logger.setLevel(logging.DEBUG)
    file_logger = logging.FileHandler('debug_log.txt', encoding='UTF-8')
    file_logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    file_logger.setFormatter(formatter)
    logger.addHandler(file_logger)
    argparser = configargparse.ArgParser(default_config_files=['sender_config.ini'])
    argparser.add('-H', '--host', required=True, help='host')
    argparser.add('-s', '--send_port', required=True, help='port to send messages')
    argparser.add('-k,', '--key', help="user's account hash")
    argparser.add('-n', '--name', help="user's nickname")
    args, _ = argparser.parse_known_args()
    try:
        writer, nickname, key = await get_sender_connection(
            args.host,
            args.send_port,
            name=args.name,
            key=args.key
        )
    except WrongHash:
        print('Неизвестный токен. Проверьте его или удалите из конфигурациии для повторной регистрации.')
        return
    args.name = nickname
    args.key = key
    config_to_write = [f"{key} = {value}\n" for key, value in args._get_kwargs()]
    with open('sender_config.ini', 'w') as file:
        file.writelines(config_to_write)


    message = 'Hello World! \n\n'
    writer.write(message.encode('UTF-8'))
    logger.debug(f"sent {message}")
    await writer.drain()

asyncio.run(main())
