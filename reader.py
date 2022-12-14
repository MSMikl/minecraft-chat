import aiofiles
import asyncio
import datetime

import configargparse

from contextlib import asynccontextmanager

@asynccontextmanager
async def get_connection(host, port):
    reader, writer = await asyncio.open_connection(host, port)
    try:
        yield reader, writer
    finally:
        writer.close()
        await writer.wait_closed()

async def main():
    argparser = configargparse.ArgParser(default_config_files=['config.ini'])
    argparser.add('-H', '--host', required=True, help='host')
    argparser.add('-p', '--recieve_port', required=True, help='port to recieve messages')
    argparser.add('-l', '--logs', required=True, help='log file name')
    args, _ = argparser.parse_known_args()

    async with get_connection(args.host, int(args.recieve_port)) as connection:
        reader, _ = connection
        while True:
            async with aiofiles.open(args.logs, 'a') as file:
                message = await reader.read(1000)
                text_line = f"[{datetime.datetime.now().strftime('%d.%m.%y %H:%M')}] {message.decode('UTF-8')}"
                await file.write(text_line)
                print(text_line)


if __name__ == '__main__':
    asyncio.run(main())
