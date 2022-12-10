import aiofiles
import asyncio
import datetime

import configargparse


async def main():
    argparser = configargparse.ArgParser(default_config_files=['config.ini'])
    argparser.add('-H', '--host', required=True, help='host')
    argparser.add('-r', '--recieve_port', required=True, help='port to recieve messages')
    argparser.add('-l', '--logs', required=True, help='log file name')
    args, _ = argparser.parse_known_args()

    reader, _ = await asyncio.open_connection(args.host, int(args.recieve_port))

    while True:
        async with aiofiles.open(args.logs, 'a') as file:
            data = await reader.read(1000)
            text_line = f"[{datetime.datetime.now().strftime('%d.%m.%y %H:%M')}] {data.decode('UTF-8')}"
            await file.write(text_line)
            print(text_line)

asyncio.run(main())
