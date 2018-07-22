import asyncio
from aiohttp import web
from os import environ
from os.path import expanduser
import sys
from BastionSiege import Siege
from telethon import TelegramClient

logfile = expanduser("~") + '/.hidden/robots.log'
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

sieges = [Siege(client[0], client[1]) for client in clients]
routines = [siege.run() for siege in sieges]


async def handle(request):
    name = request.match_info.get('name', "Anonymous")
    text = "No session for " + name
    for siege in sieges:
        if siege.telegram.session.filename.split('.')[0] == name:
            text = ""
            for k, v in siege.city.__dict__.items():
                text += str(k) + ": " + str(v) + "\n"
            continue
    return web.Response(text=text)
app = web.Application()
app.add_routes([web.get('/', handle),
                web.get('/{name}', handle)])
runner = web.AppRunner(app)


async def main():
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()
    await asyncio.gather(*routines)
    await runner.cleanup()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
