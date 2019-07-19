import asyncio
import logging
import names
import random
import string
import time
import traceback
from aiohttp import web
from os import environ
from os.path import expanduser
import sys
from BastionSiege import Siege, pretty_seconds
from telethon import TelegramClient
from telethon.errors import PhoneNumberBannedError, PhoneNumberOccupiedError

home_folder = expanduser("~")
siege_log_file = home_folder + '/.hidden/siege.log'
robots_log_file = home_folder + '/.hidden/robots.log'

log = logging.getLogger("robots")
log.propagate = False
log.setLevel(logging.DEBUG)
handler = logging.FileHandler(robots_log_file, 'a+', 'utf-8')
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(message)s'))
log.addHandler(handler)

logging.basicConfig(handlers=[logging.FileHandler(siege_log_file, 'a+', 'utf-8')],
                    level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
logging.getLogger('telethon').setLevel(logging.CRITICAL)
logging.getLogger('asyncio').setLevel(logging.CRITICAL)
logging.getLogger('aiohttp.access').setLevel(logging.CRITICAL)


def get_config():
    result = []
    try:
        with open('settings.cfg', 'r', encoding='utf-8') as file:
            for line in file:
                result.append(line.split(','))
    except FileNotFoundError:
        log.critical("missing config: make settings.cfg with config in the format session,mode,phone")
        sys.exit(1)
    return result


configs = get_config()
clients = []
for config in configs:
    log.info("starting session '" + config[0] + "'")
    try:
        clients.append([
            TelegramClient(
                config[0],
                environ['TG_API_ID'],
                environ['TG_API_HASH'],
                proxy=None,
            ).start(config[2]),
            int(config[1])
        ])
    except PhoneNumberBannedError:
        log.warning("The phone number associated with '" + config[0] + "' is banned from telegram. [TODO autoremove]")
new_client = None

sieges = [Siege(client[0], client[1]) for client in clients]


async def siege_debug_handler(request):
    name = request.match_info.get('name', "Anonymous")
    text = "No session for " + name
    for siege in sieges:
        if siege.telegram.session.filename.split('.')[0] == name:
            text = ""
            for k, v in siege.city.__dict__.items():
                text += str(k) + ": " + str(v) + "\n"
            continue
    return web.Response(text=text)


async def siege_wake_handler(request):
    name = request.match_info.get('name', None)
    if name is not None:
        for siege in sieges:
            if siege.telegram.session.filename.split('.')[0] == name:
                if siege.sleep is not None:
                    siege.sleep.cancel()
                    return web.Response(text="woke " + name)
                else:
                    return web.Response(text=name + " wasn't sleeping")
    else:
        return web.Response(text="Session not found")


async def siege_action_handler(request):
    name = request.match_info.get('name', None)
    if name is not None:
        for siege in sieges:
            if siege.telegram.session.filename.split('.')[0] == name:
                action = request.match_info.get('action', None)
                info = '\nPossible actions:\n'
                for i, button in enumerate(siege.buttons.__dict__.keys(), start=1):
                    info += f'{i}: {button}\n'
                if action is not None:
                    if hasattr(siege.buttons, action):
                        await getattr(siege.buttons, action)
                        delattr(siege.buttons, action)
                        return web.Response(text=f'{name} has called {action}!{info}')
                    else:
                        return web.Response(text=f'{name} has no action called {action}{info}')
                else:
                    return web.Response(text=f'action undefined{info}')
    else:
        return web.Response(text="Session not found")


async def siege_dashboard_handler(request):
    name = request.match_info.get('name', None)
    if name is not None:
        text = ''

        slaves = []
        refs = 0
        recents = 0
        maxref = -1
        minref = 9999

        for siege in sieges:
            session = siege.telegram.session.filename.split('.')[0]
            if session == name:
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
                text += "Upgrade priority: " + siege.get_building_to_upgrade() + "\n"
                text += getattr(siege.city, 'construction_estimate', '') + "\n"
                text += getattr(siege.city, 'goal_estimate', '')
                text += "\n\n"
            else:
                slaves.append(session)
                if hasattr(siege.city, 'townhall'):
                    town = siege.city.townhall
                    if town < 27:
                        if town > 24:
                            recents += 1
                        else:
                            refs += 1
                            if town < minref:
                                minref = town
                            if town > maxref:
                                maxref = town
                else:
                    text += f'{session} has not parsed buildings yet\n'
        text += f'slaves: {slaves}\n'
        text += f'{refs} referrals in training. {recents} recently awarded. Highest level is {maxref} and lowest is '
        text += f'{minref if minref is not 9999 else -1}\n'
        return web.Response(text=text)
    else:
        return web.Response(text="Session not found")


def save_session(session, number):
    f = open("settings.cfg", "a")
    f.write(f'\n{session},0,{number}')
    f.close()


async def siege_signup_handler(request):
    global new_client
    number = request.match_info.get('number', None)
    code = request.match_info.get('code', None)

    if new_client is None or code is None:
        session = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
        new_client = TelegramClient(
            session,
            environ['TG_API_ID'],
            environ['TG_API_HASH'],
            proxy=None,
        )
        await new_client.connect()
        try:
            await new_client.send_code_request(phone=number, force_sms=True)
        except PhoneNumberBannedError:
            return web.Response(text=f'The number {number} is banned from Telegram')
        return web.Response(text=f'get your code at {number} and append to the url')
    else:
        try:
            await new_client.sign_up(code, names.get_first_name())
            message = 'signed up!'
        except PhoneNumberOccupiedError:
            await new_client.sign_in(number, code)
            message = 'signed in to existing account!'
        session = new_client.session.filename.split('.')[0]
        save_session(session, number)
        new_siege = Siege(new_client, 0)
        sieges.append(new_siege)
        asyncio.ensure_future(new_siege.run())
        new_client = None
        return web.Response(text=message)

app = web.Application()
app.add_routes([web.get('/', siege_debug_handler),
                web.get('/create/{number}', siege_signup_handler),
                web.get('/create/{number}/{code}', siege_signup_handler),
                web.get('/{name}', siege_dashboard_handler),
                web.get('/{name}/wake', siege_wake_handler),
                web.get('/{name}/debug', siege_debug_handler),
                web.get('/{name}/{action}', siege_action_handler)])
runner = web.AppRunner(app)


async def main():
    while True:
        start = int(time.time())
        try:
            await runner.setup()
            site = web.TCPSite(runner, 'localhost', 8080)
            await site.start()
            await asyncio.gather(*[siege.run() for siege in sieges])
        except Exception:
            log.error(traceback.format_exc())
        finally:
            await runner.cleanup()
        diff = int(time.time()) - start
        log.info(f'runtime: {pretty_seconds(diff)}')
        if diff < 10:
            log.warning("will retry in fifteen minutes")
            await asyncio.sleep(900)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
