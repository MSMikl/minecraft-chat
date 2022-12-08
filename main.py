import aiofiles
import asyncio
import datetime


async def main():
    reader, writer = await asyncio.open_connection('minechat.dvmn.org', 5000)
    while True:
        async with aiofiles.open('log.txt', 'a') as file:
            data = await reader.readline()
            text_line = f"[{datetime.datetime.now().strftime('%d.%m.%y %H:%M')}] {data.decode('UTF-8')}"
            await file.write(text_line)
            print(text_line)

asyncio.run(main())
