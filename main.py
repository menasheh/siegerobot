import asyncio
from aiohttp import web
from os import environ
from os.path import expanduser
import sys
from BastionSiege import Siege, pretty_seconds
from telethon import TelegramClient


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
        int(config[1])
    ])
# todo use a logger instead of std
logfile = expanduser("~") + '/.hidden/robots.log'
output = open(logfile, 'a+', 1)
sys.stdout = output
sys.stderr = output

sieges = [Siege(client[0], client[1]) for client in clients]
routines = [siege.run() for siege in sieges]


async def handle(request):
    name = request.match_info.get('name', "Anonymous")
    text = "No session for " + name
    for siege in sieges:
        if siege.telegram.session.filename.split('.')[0] == name:
            text = ""
            buildings = [["storage", "🏤"], ["townhall", "🏚"], ["houses", "🏘"], ["farm", "🌻"], ["sawmill", "🌲"],
                         ["mine", "⛏"], ["barracks", "🛡"], ["walls", "🏰"], ["trebuchet", "⚔"]]
            upgrowth = siege.get_upgrade_income_growth()
            text += "Icon\tBuilding\tLevel\tUp💰\tEUC\tPBP\n"
            for i in range(0, len(buildings)):
                if hasattr(siege.city, buildings[i][0]):
                    text += buildings[i][1] + "\t" + buildings[i][0] + "\t"
                    if len(buildings[i][0]) < 8:
                        text += "\t"
                    text += str(getattr(siege.city, buildings[i][0])) + "\t" + str(upgrowth[buildings[i][0]]) + "\t"
                    text += str(siege.get_upgrade_equivalent_cost(buildings[i][0])) + "\t"
                    period = siege.get_upgrade_payback_period(buildings[i][0])
                    text += ("" if period is -1 else pretty_seconds(60 * period)) + "\n"
            text += "\n"
            text += "Upgrade priority: " + siege.get_building_to_upgrade()
            text += "\n\n\n\n\n"
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
