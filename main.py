import asyncio
from os import environ
from os.path import expanduser
import sys
from BastionSiege import Siege
from telethon import TelegramClient

logfile = expanduser("~") + '/.hidden/siege.log'
output = open(logfile, 'a+', 1)
sys.stdout = output
sys.stderr = output

modes = [
    ['houses', 'townhall', 'storage'],
    ['walls', 'barracks', 'trebuchet', 'houses', 'townhall', 'storage'],
]


def get_config():
    result = []
    try:
        with open('settings.cfg', 'r', encoding='utf-8') as file:
            for line in file:
                result.append(line.split(','))
    except FileNotFoundError:
        print("missing config: make settings.cfg with config in the format session,mode,phone")
        sys.exit(1)
    return result


configs = get_config()

clients = []

for config in configs:
    print("starting session '" + config[0] + "'")
    clients.append([
        TelegramClient(
            config[0],
            environ['TG_API_ID'],
            environ['TG_API_HASH'],
            proxy=None,
        ).start(config[2]),
        modes[int(config[1])]
    ])

robots = [Siege(client[0], client[1]).run() for client in clients]


async def main():
    await asyncio.gather(*robots)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
