import aiofiles
import asyncio
import datetime

import configargparse


async def main():
    argparser = configargparse.ArgParser(default_config_files=['config.ini'])
    argparser.add('-H', '--host', required=True, help='host')
    argparser.add('-p', '--port', required=True, help='port')
    args = argparser.parse_args()
    reader, writer = await asyncio.open_connection(args.host, int(args.port))
    while True:
        async with aiofiles.open('log.txt', 'a') as file:
            data = await reader.readline()
            text_line = f"[{datetime.datetime.now().strftime('%d.%m.%y %H:%M')}] {data.decode('UTF-8')}"
            await file.write(text_line)
            print(text_line)

asyncio.run(main())
