import aiofiles
import asyncio
import datetime
import json

import configargparse


async def get_sender_connection(host, port, name='Default', key=None):
    reader, writer = await asyncio.open_connection(host, port)
    answer = await reader.readline()
    print(answer.decode('UTF-8'))
    if not key:
        writer.write('\n'.encode('UTF-8'))
        await writer.drain()
        answer = await reader.readline()
        print(answer.decode('UTF-8'))
        writer.write(name.encode('UTF-8'))
        writer.write('\n'.encode('UTF-8'))
        await writer.drain()
    else:
        writer.write(key.encode('UTF-8'))
        writer.write('\n'.encode('UTF-8'))
        await writer.drain()
    answer = await reader.readline()
    user_data = json.loads(answer)
    nickname = user_data['nickname']
    key = user_data['account_hash']
    return writer, nickname, key


async def main():
    argparser = configargparse.ArgParser(default_config_files=['config.ini'])
    argparser.add('-H', '--host', required=True, help='host')
    argparser.add('-s', '--send_port', required=True, help='port to send messages')
    argparser.add('-k,', '--key', help="user's account hash")
    argparser.add('-n', '--name', help="user's nickname")
    args, _ = argparser.parse_known_args()

    writer, nickname, key = await get_sender_connection(
        args.host,
        args.send_port,
        name=args.name,
        key=args.key
    )
    args.name = nickname
    args.key = key
    argparser.write_config_file(args, ['config.ini'])

    writer.write('Hello World!'.encode('UTF-8'))
    writer.write('\n\n'.encode('UTF-8'))
    await writer.drain()

asyncio.run(main())
