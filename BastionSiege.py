from datetime import datetime
import asyncio
import logging
import math
import os
from os.path import expanduser
import random
import re
import sys
from telethon import events
from telethon.tl.types import (
    KeyboardButton, KeyboardButtonCallback
)
import time
import traceback

scriptStartTime = datetime.now()

logfile = expanduser("~") + '/.hidden/siege.log'
output = open(logfile, 'a+', 1)
sys.stdout = output
sys.stderr = output

logging.basicConfig(level=logging.DEBUG,
                    stream=sys.stdout,
                    format='%(asctime)s %(name)-12s %(threadName)s %(levelname)-8s %(message)s')
logging.getLogger('telethon').setLevel(logging.CRITICAL)
logging.getLogger('asyncio').setLevel(logging.CRITICAL)


class Siege(object):
    BOT_ID = int(252148344)

    def __init__(self, telegram_client, upgrade_priorities):
        self.telegram = telegram_client
        self.entity = "BastionSiegeBot"
        self.log = logging.getLogger(__name__ + ":" + self.telegram.session.filename.split('.')[0])

        class Object:
            def __init__(self, array):
                for each in array:
                    setattr(self, each, 0)

        self.city = Object(['gold', 'wood', 'stone', 'food', 'barracks', 'farm', 'mine', 'sawmill'])
        self.city.warStatus = 'peace'
        self.city.wallNeedsCheck = True
        self.status = Object(['lastMsgID', 'menuDepth'])
        self.status.menuDepth = 1
        self.city.update_times = Object([])

        self.city.warbuildings = ["trebuchet", "walls", "barracks"]
        self.city.upgrade_priorities = upgrade_priorities

    async def run(self):
        @self.telegram.on(events.NewMessage(incoming=True, from_users=self.BOT_ID))
        async def update_handler(event):
            self.status.menuDepth = 3
            message = event.message.message
            try:
                await parse_message(self, message)
            except Exception as err:
                self.log.error('Unexpected error ({}): {} at\n{}'.format(type(err), err, traceback.format_exc()))

            if event.message.reply_markup is not None:
                markup = []
                class Object:
                    pass
                chatbuttons = Object()
                chatbuttons.id = event.message.id
                chatbuttons.text = []
                chatbuttons.data = []
                for row in event.message.reply_markup.rows:
                    for button in row.buttons:
                        if type(button) is KeyboardButton:
                            markup.append(button.text)
                        elif type(button) is KeyboardButtonCallback:
                            chatbuttons.text.append(button.text)
                            chatbuttons.data.append(button.data)
                if not markup == []:
                    self.status.replyMarkup = markup
                elif not chatbuttons.text == []:
                    self.status.chatbuttons = chatbuttons
                    self.log.debug("found chatbuttons:")
                    self.log.debug(chatbuttons)
            else:
                self.log.warning("no markup associated with message " + event.message.message)
            self.status.lastMsgID = event.message.id
            # self.log.debug(" ")
            # for k, v in self.city.__dict__.items():
            #   self.log.debug(str(k) + ": " + str(v))

        await asyncio.gather(
            self.telegram.run_until_disconnected(),
            build(self)
        )


def clean_trim(string):
    return ''.join(string.split())


async def send_message_and_wait(self, message):
    start_time = time.time()
    lastid = self.status.lastMsgID
    await self.telegram.send_message(self.entity, message)
    while lastid == self.status.lastMsgID:
        await asyncio.sleep(random.randint(1000, 4000) / 1000)
        sleeptime = int(time.time() - start_time)
        if sleeptime > 200:
            self.log.error("slept " + pretty_seconds(sleeptime) + " after '" + message + "'. Problem?")
            self.log.error(traceback.format_exc())
            for k, v in self.city.__dict__.items():
                self.log.debug(str(k) + ": " + str(v))
            await inplacerestart()
        pass
    await asyncio.sleep(random.randint(600, 1000) / 1000)


def update_gold(self):
    # todo - if population wasn't maximum when gold last updated, need to either wait for it or use rate & summation...
    timediff = math.floor((time.time() - getattr(self.city.update_times, 'gold', time.time())) / 60)
    self.city.gold += timediff * getattr(self.city, 'dailyGoldProduction', 0)
    self.city.update_times.gold = time.time()


def update_resources(self):
    update_resource(self, "wood")
    update_resource(self, "stone")
    update_resource(self, "food")


def update_resource(self, resource):
    timediff = math.floor((time.time() - getattr(self.city.update_times, resource)) / 60)
    setattr(self.city, resource, getattr(self.city, resource) + timediff *
            getattr(self.city, 'daily' + resource.capitalize() + 'Production'))
    setattr(self.city.update_times, resource, time.time())


async def procrastinate(self):
    rand_time = random.randint(120, random.randint(1200, 1500 + random.randint(0, 1) * 300))
    self.log.info("snoozing for " + pretty_seconds(rand_time) + ".")
    await asyncio.sleep(rand_time)


async def environment(self):
    await return_to_main(self)
    await send_message_and_wait(self, "⚒ Workshop")  # Workshop
    await send_message_and_wait(self, "⬅️ Back")  # Back
    await send_message_and_wait(self, "🏘 Buildings")  # Buildings

    self.city.maxGold = 500000 * self.city.townhall
    self.city.dailyGoldProduction = self.city.houses * 10 + self.city.houses * self.city.townhall * 2  # Assumes max pop
    self.city.dailyPeopleIncrease = self.city.houses

    self.city.dailyWoodProduction = self.city.sawmill * 10
    self.city.dailyStoneProduction = self.city.mine * 10
    self.city.dailyFoodProduction = self.city.farm * 10

    await structure_exists(self)
    await resource_hires(self)

    self.city.maxResource = (self.city.storage * 50 + 1000) * self.city.storage
    self.city.maxWood = self.city.maxStone = self.city.maxFood = self.city.maxResource

    self.city.dailyFoodConsumption = (self.city.houses - min(self.city.farm, self.city.storage)) * 10 \
        if self.city.houses > min(self.city.farm, self.city.storage) else 0
    self.city.foodReserveHours = 8
    self.city.foodReserve = min(self.city.dailyFoodConsumption * self.city.foodReserveHours * 60, self.city.maxFood)
    self.city.foodReserveMin = self.city.foodReserve / 2

    calc_all_upgrade_costs(self)


async def structure_exists(self):
    if self.city.storage == 0:
        await send_message_and_wait(self, '🏚 Storage')
        await send_message_and_wait(self, self.status.replyMarkup[0])  # Build
        await send_message_and_wait(self, '➕ Hire')
        await employ_at_capacity(self, "storage")
        await send_message_and_wait(self, "⬅️ Back")
        await send_message_and_wait(self, "⬅️ Back")
    if self.city.farm == 0:
        await send_message_and_wait(self, '🌻 Farm')  # Farm
        await send_message_and_wait(self, self.status.replyMarkup[0])  # Build
        await send_message_and_wait(self, "➕ Hire")
        await employ_at_capacity(self, "farm")  # todo technically could detect active building from message...
        await send_message_and_wait(self, "⬅️ Back")
        await send_message_and_wait(self, "⬅️ Back")
    if self.city.sawmill == 0:
        await send_message_and_wait(self, '🌲 Sawmill')  # Sawmill
        await send_message_and_wait(self, self.status.replyMarkup[0])  # Build
        await send_message_and_wait(self, "➕ Hire")
        await employ_at_capacity(self, "sawmill")
        await send_message_and_wait(self, "⬅️ Back")
        await send_message_and_wait(self, "⬅️ Back")
    if self.city.mine == 0:
        await send_message_and_wait(self, '⛏ Mine')  # Mine
        await send_message_and_wait(self, self.status.replyMarkup[0])  # Build
        await send_message_and_wait(self, "➕ Hire")
        await employ_at_capacity(self, "mine")
        await send_message_and_wait(self, "⬅️ Back")
        await send_message_and_wait(self, "⬅️ Back")


async def employ_up_to_capacity(self, building, already):
    workers, max = get_building_employment_vars(self, building)
    missing = 0
    if getattr(self.city, workers, 0) < getattr(self.city, max, 0):
        already = await go_to_recruit(self, already)
        await send_message_and_wait(self, building.capitalize())
        missing = await employ_at_capacity(self, building, False)
        await send_message_and_wait(self, 'Back')
    return already, missing


def get_building_employment_vars(self, building):
    if building in ['storage', 'farm', 'sawmill', 'mine', 'trebuchet']:
        return building + 'Workers', building + 'MaxWorkers'
    else:
        if building == 'walls':
            return 'archers', 'maxArchers'
        else:
            if building == 'barracks':
                return 'soldiers', 'maxSoldiers'
            else:
                self.log.critical("I don't know how to employ at " + building + ".")


async def employ_at_capacity(self, building, wait=True):
    workers, max = get_building_employment_vars(self, building)

    while getattr(self.city, max, 10) > getattr(self.city, workers, 0):
        hirable = min(self.city.people, getattr(self.city, max, 10) - getattr(self.city, workers, 0))
        if hirable > 0:
            await send_message_and_wait(self, str(hirable))
        sleeptime = math.ceil(min(getattr(self.city, max, 10) - getattr(self.city, workers, 0),
                                  self.city.maxPeople) / self.city.dailyPeopleIncrease)
        if sleeptime > 0 and wait:
            self.log.info("Sleeping " + pretty_seconds(60 * sleeptime) + " to get more workers for " + building + ".")
            await asyncio.sleep(60 * sleeptime)
            await send_message_and_wait(self, str(sleeptime * self.city.dailyPeopleIncrease))
        else:
            return getattr(self.city, max, 10) - getattr(self.city, workers, 0)


async def resource_hires(self):
    for x in ['storage', 'farm', 'sawmill', 'mine']:
        workers, max = x + 'Workers', x + 'MaxWorkers'
        if getattr(self.city, workers) < getattr(self.city, max):
            await send_message_and_wait(self, x.capitalize())
            await send_message_and_wait(self, "➕ Hire")
            await employ_at_capacity(self, x)
            await send_message_and_wait(self, "⬅️ Back")
            await send_message_and_wait(self, "⬅️ Back")


def calc_all_upgrade_costs(self):
    calc_upgrade_costs(self, 'sawmill')
    calc_upgrade_costs(self, 'mine')
    calc_upgrade_costs(self, 'farm')
    calc_upgrade_costs(self, 'houses')
    calc_upgrade_costs(self, 'townhall')
    if hasattr(self.city, "barracks") and (self.city.barracks != 0):
        calc_upgrade_costs(self, 'barracks')
    if hasattr(self.city, "walls") and (self.city.walls != 0):
        calc_upgrade_costs(self, 'walls')
    if hasattr(self.city, "trebuchet") and (self.city.trebuchet != 0):
        calc_upgrade_costs(self, 'trebuchet')
    calc_upgrade_costs(self, 'storage')


def calc_upgrade_costs(self, building):
    results = upgrade_costs(building, getattr(self.city, building) + 1)
    suffix = ['Cost', 'Wood', 'Stone']

    for x in range(0, 3):
        setattr(self.city, building + 'Upgrade' + suffix[x], results[x])


def upgrade_costs(building, level_desired):
    coeff = {
        'sawmill': [100, 50, 50],
        'mine': [100, 50, 50],
        'farm': [100, 50, 50],
        'houses': [200, 100, 100],
        'townhall': [500, 200, 200],
        'barracks': [200, 100, 100],
        'walls': [5000, 500, 1500],
        'trebuchet': [8000, 1000, 300],
        'storage': [200, 100, 100]
    }

    level_current = level_desired - 1
    level_previous = level_desired - 2

    resources_sunk = -2
    if level_current > 0:
        resources_sunk = level_current * level_previous * ((2 * level_current + 8) / 6 + 2 / level_current)

    result = [0, 0, 0]

    for x in range(0, 3):
        result[x] = int((coeff[building][x] * (level_desired * level_current * (
                (2 * level_desired + 8) / 6 + 2 / level_desired) - resources_sunk)) / 2)

    return result


async def return_to_main(self):
    if self.status.menuDepth > 0:
        await send_message_and_wait(self, '⬆️ Up menu')


def human_readable_indexes(self, message):
    for i in range(0, len(message.split())):
        print(str(i) + ": " + message.split()[i])


async def parse_message(self, message):
    message = message.replace(u'\u200B', '')
    first_line = message.split()[0]
    # Main Info and Buildings
    if 'Season' in message:
        parse_profile(self, message)
    elif 'Buildings' in message:
        parse_buildings_profile(self, message)
    elif 'Wins' in message and 'rating' not in message:
        parse_war_profile(self, message)
    elif 'Town hall' in message:
        parse_building_town_hall(self, message)
    elif '🏘Houses' in message.split()[0]:
        parse_building_houses(self, message)
    elif 'Resources' in first_line or 'no place in the storage' in message or 'find money.' in message:
        await parse_resource_message(self, message)
    elif 'Storage' in first_line and '👥' in message:
        parse_building_storage(self, message)
    elif 'Barracks' in first_line:
        parse_building_barracks(self, message)
    elif 'Walls' in first_line and '👥' in message:
        parse_building_walls(self, message)
    elif 'Sawmill' in first_line and '👥' in message:
        parse_building_sawmill(self, message)
    elif 'Mine' in first_line:
        parse_building_mine(self, message)
    elif 'Farm' in first_line:
        parse_building_farm(self, message)
    elif 'Workshop' in first_line:
        parse_workshop(self, message)
    elif 'Trebuchet' in first_line and '👥' in message:
        parse_trebuchet(self, message)
    # War
    elif 'Info' in message.split()[0]:
        parse_war_recruitment_info(self, message)
    elif 'Our scouts' in message:
        parse_scout_message(self, message)
    elif 'Choose number.' in message:
        self.status.expects = 'chooseNumber'
    elif 'Siege has started!' in message:
        self.city.warStatus = 'attack'
    elif 'Congratulations' in message and 'army' in message:  # remove army part once alliance parser made
        # if 'army' in message:
        parse_war_victory(self, message)
        # elif 'alliance' in message:
        #   parse_war_clan_victory(self, message)
    elif 'Your domain attacked!' in message:
        parse_war_attacked(self, message)
    elif 'your army lose' in message:
        parse_war_defeat(self, message)
    # Clan War
    elif 'help him in the attack' in message:
        parse_war_clan_attack(self, message)
    elif 'help defend' in message:
        parse_war_clan_defend(self, message)
    # elif 'The' in message.split()[0]:  # This was probably NOT intended as a catch all...
    #    parse_war_clan_join(self, message)
    elif 'your alliance lose' in message:
        parse_war_clan_defeat(self, message)
    # skip some message types
    elif 'joined the attack' in message:
        pass
    elif 'not yet recovered' in message:
        pass
    elif 'Welcome to the alliance' in message:
        pass
    elif 'statistic' in message:
        pass
    else:
        self.log.error('unknown message type')
        self.log.error(message)


def parse_numbers_from_message(self, msg, numbers):
    t = re.findall(r'(-?\d+)', msg)

    try:
        for i in range(0, len(numbers)):
            setattr(self.city, numbers[i], int(t.pop(0)))
    except IndexError:
        self.log.error("incorrect numbers? Message:\n" + msg + "\n" + "numbers:\n" + str(numbers))


def debug_numbers_from_message(self, msg):
    self.log.debug(msg)
    t = re.findall(r'(-?\d+)', msg)
    i = 0
    for j in t:
        self.log.debug(str(i) + ": " + j)
        i += 1


def try_regex(self, regex, msg, method):  # todo get method from call stack
    match = re.match(regex, msg)
    if match is None:
        self.log.critical("REGEX ERROR:")
        self.log.critical("\t" + method + " could not parse:\n" + msg + "\n</msg>\n")
        exit(1)
    return match


def parse_profile(self, msg):
    match = try_regex(self, r'(\W+?)?(?:{(.+)})?(?:\[(\W)])?([\w ]+).+ory\d+🗺Season(\w+.+)Weather(\w+).+',
                      clean_trim(msg), "parse_profile")

    parse_numbers_from_message(self, msg,
                               ['territory', 'time.hour', 'time.minute', 'time.second', 'people', 'soldiers',
                                'gems', 'gold', 'wood', 'stone', 'food'])

    msg = msg.split()
    self.city.statuses = match.group(1) or ""
    self.city.achievements = match.group(2) or ""
    self.city.alliance = match.group(3) or ""
    self.city.governor = re.compile('[\W_ ]+').sub('', msg[0])
    self.city.name = msg[1]
    self.city.status = msg[3]
    self.city.season = match.group(5)
    self.city.weather = match.group(6)

    self.city.update_times.people = time.time()
    self.city.update_times.gold = time.time()
    self.city.update_times.wood = time.time()
    self.city.update_times.stone = time.time()
    self.city.update_times.food = time.time()

    self.status.menuDepth = 0


def parse_buildings_profile(self, msg):
    match = try_regex(self,
                      r'.+🏤([0-9]+)([⛔,✅]).?(?:🏚([0-9]+)([⛔,✅])\D?([0-9]+)/([0-9]+)👥)?🏘([0-9]+)([⛔,✅])\D?([0-9]+)/'
                      r'([0-9]+)👥(?:🌻([0-9]+)([⛔,✅])\D?([0-9]+)/([0-9]+)👥)?(?:🌲([0-9]+)([⛔,✅])\D?([0-9]+)/([0-9]+)👥)'
                      r'?(?:⛏([0-9]+)([⛔,✅])\D?([0-9]+)/([0-9]+)👥)?(?:🛡([0-9]+)([⛔,✅])\D?([0-9]+)/([0-9]+)⚔)?(?:🏰(['
                      r'0-9]+)([⛔,✅])\D?([0-9]+)/([0-9]+))?(?:🏹)?.+', clean_trim(msg), "parse_buildings_profile")

    # debug_numbers_from_message(self, msg)
    # TODO - handle missing buildings better when using numbers method

    numbers = ['townhall', 'storage', 'storageWorkers', 'storageMaxWorkers', 'houses', 'people', 'maxPeople', 'farm',
               'farmWorkers', 'farmMaxWorkers', 'sawmill', 'sawmillWorkers', 'sawmillMaxWorkers', 'mine', 'mineWorkers',
               'mineMaxWorkers', 'barracks', 'soldiers', 'maxSoldiers', 'walls', 'archers', 'maxArchers']

    self.city.townhall = int(match.group(1))
    self.city.storage = int(match.group(3) or 0)
    if self.city.storage > 0:
        self.city.storageWorkers = int(match.group(5))
        self.city.storageMaxWorkers = int(match.group(6))
    self.city.houses = int(match.group(7))
    self.city.people = int(match.group(9))
    self.city.maxPeople = int(match.group(10))
    self.city.farm = int(match.group(11) or 0)
    if self.city.farm > 0:
        self.city.farmWorkers = int(match.group(13))
        self.city.farmMaxWorkers = int(match.group(14))
    self.city.sawmill = int(match.group(15) or 0)
    if self.city.sawmill > 0:
        self.city.sawmillWorkers = int(match.group(17))
        self.city.sawmillMaxWorkers = int(match.group(18))
    self.city.mine = int(match.group(19) or 0)
    if self.city.mine > 0:
        self.city.mineWorkers = int(match.group(21))
        self.city.mineMaxWorkers = int(match.group(22))
    self.city.barracks = int(match.group(23) or 0)
    if self.city.barracks > 0:
        self.city.soldiers = int(match.group(25))
        self.city.maxSoldiers = int(match.group(26))
    self.city.walls = int(match.group(27) or 0)
    if self.city.walls > 0:
        self.city.archers = int(match.group(29))
        self.city.maxArchers = int(match.group(30))

    self.status.menuDepth = 1  # keeps track of back - up might be different


def parse_war_profile(self, msg):
    numbers = [
        'wins', 'karma', 'territory', 'time.hour', 'time.minute', 'time.second', 'wall', 'maxWall', 'archers',
        'maxArchers', 'food',
    ]
    parse_numbers_from_message(self, msg, numbers)

    reg = re.compile(
        r'(⛔️|✅).+?(⛔️|✅)(?:.+Next attack - (\d+) (min|sec)\.)?(?:.+Next ally attack - (\d+) (min|sec)\.)?'
        #   1         2                        3       4                                 5       6
        r'(?:.+No attacks - (\d+) (min|sec)\.)?(.+Continues the battle with( alliance)? \[?(\W?)]?([\w ]'
        #                     7       8          9                             10            11     12
        #                 13           14
        r'+)(?:\nAttack: (.+)Defence: (.+))?)?', re.S)
    m = re.search(reg, msg)

    self.city.canAttack = False if '⛔' in m.group(1) + m.group(2) else True
    if m.group(3) is None:
        self.city.cooldownAttack = 0
    else:
        self.city.cooldownAttack = int(m.group(3)) * (1 if m.group(4) is "sec" else 60)
    if m.group(5) is None:
        self.city.cooldownAttackClan = 0
    else:
        self.city.cooldownAttackClan = int(m.group(5)) * (1 if m.group(6) is "sec" else 60)
    if m.group(7) is None:
        self.city.cooldownDefense = 0
    else:
        self.city.cooldownDefense = int(m.group(7)) * (1 if m.group(8) is "sec" else 60)
    self.city.update_times.cooldowns = time.time()
    if m.group(9) is None:
        self.city.warStatus = 'peace'
        self.city.currentEnemyClan = ''
        self.city.currentEnemyClanName = ''
        self.city.currentEnemyName = ''
    else:
        if m.group(10) is None:
            self.city.currentEnemyClan = m.group(11)
            self.city.currentEnemyName = m.group(12)
        else:
            self.city.currentEnemyClan = m.group(11)
            self.city.currentEnemyClanName = m.group(12)
            if self.city.governor in m.group(
                    13):
                self.city.warStatus = 'clanAttack'
                self.city.currentClanWarEnemies = m.group(30)
                self.city.currentClanWarFriends = m.group(29)
                self.city.currentClanWarEnemyCount = len(self.city.currentClanWarEnemies.split(','))
                self.city.currentClanWarFriendCount = len(self.city.currentClanWarFriends.split(','))
                self.log.debug("check if first => attacking")
            elif self.city.governor in m.group(
                    14):  # defending
                self.city.warStatus = 'clanDefence'
                self.city.currentClanWarEnemies = m.group(29)
                self.city.currentClanWarFriends = m.group(30)
                self.city.currentClanWarEnemyCount = len(self.city.currentClanWarEnemies.split(','))
                self.city.currentClanWarFriendCount = len(self.city.currentClanWarFriends.split(','))
                self.log.debug("check if first => defending")
                # TODO More useful if other bot receives such messages and sends them on here, to aid in decision of
                #  attacking or not.
            else:
                self.log.warning("Could not find self %s in current clan battle!" % self.city.governor)

    self.status.menuDepth = 1


def parse_war_recruitment_info(self, msg):
    parse_numbers_from_message(self, msg, ['soliders', 'maxSoldiers', 'archers', 'maxArchers', 'trebuchetWorkers',
                                           'maxTrebuchetWorkers'])
    self.status.menuDepth = 2


async def parse_resource_message(self, msg):
    if 'delivered' in msg:
        'resources purchased'
    if 'find money.' in msg:
        self.log.error('not enough money for resources')
        await send_message_and_wait(self, "1")  # Remind script of actual resource amount by purchasing 1
    if 'no place' in msg:
        self.log.error('no room for resources we attempted to purchase')
    else:
        parse_numbers_from_message(self, msg, ['gems', 'gold', 'wood', 'stone', 'food'])

        self.city.update_times.gems = time.time()
        self.city.update_times.gold = time.time()
        self.city.update_times.wood = time.time()
        self.city.update_times.stone = time.time()
        self.city.update_times.food = time.time()

        #  Technically speaking I could just hardcode 2 or use a resourcePrice variable...
        self.city.woodPrice = 2
        self.city.stonePrice = 2
        self.city.foodPrice = 2

    self.status.menuDepth = 1


def parse_scout_message(self, msg):
    parse_numbers_from_message(self, msg, ['enemyTerritory', 'enemyKarma'])

    """
    friends = "🐄🦋🛰⚡"

    if any((c in friends) for c in msg):
        send_message_and_wait(self, "Suitable")
    """

    msg = msg.split()

    tmp = msg.index('domain') + 1
    tmp2 = msg.index('with') - 1
    self.city.enemyDomain = msg[tmp]
    if tmp2 != tmp:
        for i in range(1, tmp2 - tmp):
            self.city.enemyDomain += " " + msg[tmp + i]

    self.status.menuDepth = 1


def parse_building_barracks(self, msg):
    parse_numbers_from_message(self, msg, [
        'barracks', 'soldiers', 'maxSoldiers', 'barracksRecruitCostGold', 'barracksRecruitCostFood',
        'barracksRecruitCostPeople', 'gold', 'people', 'barracksUpgradeCost', 'barracksUpgradeWood',
        'barracksUpgradeStone'
    ])

    self.status.menuDepth = 2


def parse_building_farm(self, msg):
    parse_numbers_from_message(self, msg, ['farm', 'farmWorkers', 'farmMaxWorkers', 'farmLocalStorage',
                                           'farmMaxLocalStorage', 'dailyFoodProduction', 'dailyFoodConsumption',
                                           'storageWorkers', 'farmUpgradeGold', 'farmUpgradePeople', 'gold',
                                           'people',
                                           'farmUpgradeCost', 'farmUpgradeWood', 'farmUpgradeStone'])

    self.status.menuDepth = 2


def parse_building_houses(self, msg):
    parse_numbers_from_message(self, msg, ['houses', 'people', 'maxPeople', 'dailyPeopleIncrease',
                                           'dailyFoodConsumption', 'dailyFoodProduction', 'storageWorkers',
                                           'housesUpgradeCost', 'housesUpgradeWood', 'housesUpgradeStone'])
    self.city.update_times.people = time.time()

    self.status.menuDepth = 2


def parse_building_mine(self, msg):
    reg = re.compile(r'(\d+)')
    m = re.findall(reg, msg)

    debug_numbers_from_message(self, msg)

    self.city.mine = int(m[0])
    self.city.mineWorkers = int(m[1])
    self.city.mineMaxWorkers = int(m[2])
    self.city.mineLocalStorage = int(m[3])
    # mineMaxLocalStorage
    self.city.dailyStoneProduction = int(m[5])
    self.city.storageWorkers = int(m[6])
    # Individual cost variable for hiring?
    #
    self.city.gold = int(m[9])
    self.city.update_times.gold = time.time()
    self.city.people = int(m[10])
    self.city.update_times.people = time.time()
    self.city.mineUpgradeCost = int(m[11])
    self.city.mineUpgradeWood = int(m[12])
    self.city.mineUpgradeStone = int(m[13])

    self.status.menuDepth = 2


def parse_building_sawmill(self, msg):
    reg = re.compile(r'(\d+)')
    m = re.findall(reg, msg)

    debug_numbers_from_message(self, msg)

    self.city.sawmill = int(m[0])
    self.city.sawmillWorkers = int(m[1])
    self.city.sawmillMaxWorkers = int(m[2])
    self.city.sawmillLocalStorage = int(m[3])
    # sawmillMaxLocalStorage
    self.city.dailyWoodProduction = int(m[5])
    self.city.storageWorkers = int(m[6])
    # Individual cost variable for hiring?
    #
    self.city.gold = int(m[9])
    self.city.update_times.gold = time.time()
    self.city.people = int(m[10])
    self.city.update_times.people = time.time()
    self.city.sawmillUpgradeCost = int(m[11])
    self.city.sawmillUpgradeWood = int(m[12])
    self.city.sawmillUpgradeStone = int(m[13])

    self.status.menuDepth = 2


def parse_building_storage(self, msg):
    numbers = ['storage', 'storageWorkers', 'maxStorageWorkers', 'wood', 'maxWood', 'stone', 'maxStone', 'food',
               'maxFood', 'storageHireCost', 'storageHirePeople', 'gold', 'people']
    if "Fill" in msg:
        numbers.append('storageFillCost')
    for each in ['storageUpgradeCost', 'storageUpgradeWood', 'storageUpgradeStone']:
        numbers.append(each)

    parse_numbers_from_message(self, msg, numbers)

    self.city.update_times.wood = time.time()
    self.city.update_times.stone = time.time()
    self.city.update_times.food = time.time()
    self.city.update_times.gold = time.time()
    self.city.update_times.people = time.time()

    self.status.menuDepth = 2


def parse_building_town_hall(self, msg):
    parse_numbers_from_message(self, msg,
                               ['townhall', 'gold', 'maxGold', 'dailyGoldProduction', 'townhallUpgradeCost',
                                'townhallUpgradeWood', 'townhallUpgradeStone'])
    self.city.update_times.gold = time.time()
    self.status.menuDepth = 2


def parse_building_walls(self, msg):
    reg = re.compile(
        r'(\d+)\D+(\d+)/(\d+)🏹\D+(\d+)💰(\d+)🍖/(\d+)👥\D+\+(\d+)\D+(\d+)/(\d+)\D+(\d+)\D+(\d+)👥.+(Repair|'
        r'Upgrade)\D+(\d+)💰(⛔️|✅)\D+(\d+)🌲(⛔️|✅)\D+(\d+)⛏(⛔️|✅)', re.S)
    m = re.search(reg, msg)

    self.city.walls = int(m.group(1))
    self.city.archers = int(m.group(2))
    self.city.maxArchers = int(m.group(3))
    # Individual Recruit cost? 10, 1, 1 are current values of 4, 5, 6
    self.city.wallAttackBonus = int(m.group(7))
    self.city.wallDurability = int(m.group(8))
    self.city.wallMaxDurability = int(m.group(9))
    self.city.gold = int(m.group(10))
    self.city.update_times.gold = time.time()
    self.city.people = int(m.group(11))
    self.city.update_times.people = time.time()
    self.city.wallStatus = m.group(12)
    setattr(self.city, 'walls' + self.city.wallStatus + 'Cost', int(m.group(13)))
    setattr(self.city, 'walls' + self.city.wallStatus + 'Wood', int(m.group(15)))
    setattr(self.city, 'walls' + self.city.wallStatus + 'Stone', int(m.group(17)))
    self.city.wallsCanUpgrade = False if '⛔' in m.group(14) + m.group(16) + m.group(18) else True

    self.status.menuDepth = 2


def parse_workshop(self, msg):
    reg = re.compile(r'(\d+)')
    m = re.findall(reg, msg) + [0, 0, 0]

    self.city.trebuchet = int(m[0])
    self.city.trebuchetWorkers = int(m[1])
    self.city.trebuchetMaxWorkers = int(m[2])

    self.status.menuDepth = 1


def parse_trebuchet(self, msg):
    reg = re.compile(r'(\d+)')
    m = re.findall(reg, msg)

    self.city.trebuchet = int(m[0])
    self.city.trebuchetWorkers = int(m[1])
    self.city.trebuchetMaxWorkers = int(m[2])
    # cost
    self.city.trebuchetAttackBonus = int(m[5])
    self.city.trebuchetAttack = int(m[6])
    self.city.gold = int(m[7])
    self.city.people = int(m[8])
    self.city.trebuchetUpgradeCost = int(m[9])
    self.city.trebuchetUpgradeWood = int(m[10])
    self.city.trebuchetUpgradeStone = int(m[11])

    self.status.menuDepth = 2


def parse_war_attacked(self, msg):
    match = try_regex(self, r'.+! \[?(\W?)]?(.+) approaches t.+', msg, 'parse_war_attacked')
    self.city.attackingClan = match.group(1)
    self.city.attackingPlayer = match.group(2)
    self.city.warStatus = "defend"


def parse_war_victory(self, msg):
    self.log.info(msg)

    m3 = re.search(r'(\d+)💰', msg)
    if m3 is None:
        self.city.lastBattleGold = 0
    else:
        self.city.lastBattleGold = int(m3.group(1))
    update_gold(self)
    self.city.gold += self.city.lastBattleGold

    self.city.warStatus = 'peace'

    reg = re.compile(r'with (?:{(.+)})?(?:\[(\W)])?([\w ]+) complete')
    m = re.search(reg, msg)

    self.city.lastEnemyStatuses = m.group(1) or ''
    self.city.lastEnemyClan = m.group(2) or ''
    self.city.lastEnemyName = m.group(3)

    m2 = re.search(r'winners (\d+)⚔ (?:of (\d+)⚔)?', msg)
    self.city.lastBattleReturnedSoldiers = int(m2.group(1))
    self.city.lastBattleSentSoldiers = int(m2.group(2) or m2.group(1))

    m4 = re.search('(\d+)🗺', msg)
    if m4 is None:
        self.city.lastBattleTerritory = 0
        self.city.wallNeedsCheck = True
    else:
        self.city.lastBattleTerritory = int(m4.group(1))

    if not hasattr(self.city, "soldiers"):
        self.city.soldiers = 0
    self.city.soldiers = max(self.city.soldiers + self.city.lastBattleReturnedSoldiers, self.city.barracks * 40)
    self.city.territory += self.city.lastBattleTerritory


def parse_war_defeat(self, msg):
    self.log.info(msg)

    update_gold(self)
    m2 = re.search(r'(\d+)💰', msg)
    if m2 is None:
        self.city.lastBattleGold = 0
    else:
        self.city.lastBattleGold = int(m2.group(1))
        self.city.gold = self.city.gold - self.city.lastBattleGold

    self.city.warStatus = 'peace'

    reg = re.compile(
        r'with 🗡?(?:{(.+)})?(?:\[(\W)])?([\w, ]+) complete. Unfortunately, ([\w ]+),.+ lose\. (None|Only'
        r' (\d+)⚔) of (\d+)⚔')

    m = re.search(reg, msg)

    self.city.lastEnemyStatuses = m.group(1)
    self.city.lastEnemyClan = m.group(2)
    self.city.lastEnemyName = m.group(3)
    self.city.governor = m.group(4)
    if m.group(6) is not None:
        self.city.soldiers = self.city.soldiers + int(m.group(6))
    self.city.soldiersInPreviousBattle = int(m.group(7))

    m3 = re.search('(\d+)🗺', msg)
    if m3 is None:
        self.city.lastBattleTerritory = 0
    else:
        self.city.wallNeedsCheck = True
        self.city.lastBattleTerritory = int(m3.group(1))


def parse_war_clan_defeat(self, msg):
    self.log.info(msg)
    self.log.error('not implemented for above message')

    debug_numbers_from_message(self, msg)


def parse_war_clan_join(self, msg):
    self.log.warning('parsing join - needs reg and inline')
    human_readable_indexes(self, msg)

    debug_numbers_from_message(self, msg)


def parse_war_clan_attack(self, msg):
    self.log.info(msg)

    match = try_regex(self, r'Your ally \W?(?:{.+})?\[(.)](.+) attacked \W?(?:{.+})?\[(.)](.+) from the alliance '
                            r'\[.](.+)! Y.+', msg, 'parse_war_clan_attack')

    self.city.alliance = match.group(1)
    self.city.clanAllyAttacking = match.group(2)
    self.city.clanDefendingAllianceSymbol = match.group(3)
    self.city.clanDefendingPlayer = match.group(4)
    self.city.clanDefendingAllianceName = match.group(5)


def parse_war_clan_defend(self, msg):
    self.log.info(msg)

    match = try_regex(self,
                      r'Your ally \W?(?:{.+})?\[(.)](.+) was attacked by \W?(?:{.+})?\[(.)](.+) from \[.](.+)! '
                      r'Y.+', msg, 'parse_war_clan_defend')

    self.city.alliance = match.group(1)
    self.city.clanAllyUnderAttack = match.group(2)
    self.city.clanAttackingAllianceSymbol = match.group(3)
    self.city.clanAttackingPlayer = match.group(4)
    self.city.clanAttackingAllianceName = match.group(5)
    # todo get way to defend (inline keyboard)


def pretty_print(objecty):
    for i in range(0, len(objecty)):
        print(i, objecty[i])


async def build(self):
    await environment(self)
    while True:
        if self.city.warStatus is 'peace':
            if getattr(self.city, 'walls', 0) > 0:
                await return_to_main(self)
                if self.city.wallNeedsCheck or wall_needs_repair(self):
                    await send_message_and_wait(self, "Buildings")
                    await send_message_and_wait(self, "Walls")
                    if wall_needs_repair(self):
                        if self.city.wallsCanUpgrade:
                            await send_message_and_wait(self, "Repair")
                        else:
                            self.log.warning("Can't repair walls. Buy items?")
                    self.city.wallNeedsCheck = False
                already = False
                missing = 0
                i = 0
                while missing == 0 and i < len(self.city.warbuildings):
                    already, missing = await employ_up_to_capacity(self, self.city.warbuildings[i], already)
                    i += 1
                if already:
                    await send_message_and_wait(self, "⬆️ Up menu")

            buildings = self.city.upgrade_priorities
            i = 0
            while self.city.maxWood < getattr(self.city, buildings[i] + 'UpgradeWood') or \
                    self.city.maxStone < getattr(self.city, buildings[i] + 'UpgradeStone') or \
                    self.city.maxGold < getattr(self.city, buildings[i] + 'UpgradeCost'):
                i += 1

            await return_to_main(self)
            requiredfood = await purchase_resource(self, "food", get_food_purchase_quantity_for_reserve(self))
            requiredwood = await purchase_resource(self, "wood",
                                             get_upgrade_required_resource_quantity(self, buildings[i], "wood"))
            requiredstone = await purchase_resource(self, "stone",
                                              get_upgrade_required_resource_quantity(self, buildings[i], "stone"))
            requiredgold = getattr(self.city, buildings[i] + 'UpgradeCost') - self.city.gold

            estimatedtime = get_estimated_time_to_resources(self, requiredgold, requiredfood, requiredwood,
                                                            requiredstone)

            if estimatedtime > 0:
                self.log.info(
                    "Upgrade of " + buildings[i] + " possible in approximately " + pretty_seconds(
                        60 * estimatedtime) + ".")
                goldreq = 0
                woodreq = 0
                stonereq = 0
                leveldesired = getattr(self.city, buildings[i])
                while self.city.maxWood > woodreq and self.city.maxStone > stonereq and self.city.maxGold > goldreq:
                    leveldesired += 1
                    goldreq, woodreq, stonereq = upgrade_costs(buildings[i], leveldesired)
                    requiredgold += goldreq
                    requiredwood += woodreq
                    requiredstone += stonereq
                leveldesired -= 1
                requiredgold -= goldreq
                requiredwood -= woodreq
                requiredstone -= stonereq

                estimatedtime = get_estimated_time_to_resources(self, requiredgold, requiredfood, requiredwood,
                                                                requiredstone)
                self.city.goal_estimate = "With %d storage, %s maxes out at %d and will take ~%s to complete." % (
                    self.city.storage, buildings[i], leveldesired, pretty_seconds(60 * estimatedtime)
                )
                self.log.info(self.city.goal_estimate)
                await procrastinate(self)
                update_gold(self)
                update_resources(self)
            else:
                await upgrade_building(self, buildings[i])
        else:
            await asyncio.sleep(1)


def get_estimated_time_to_resources(self, gold, food, wood, stone):
    return max(0, int(math.ceil((gold + 2 * (food + wood + stone)) / self.city.dailyGoldProduction)))


def get_purchasable_resource_quantity(self, quantity):
    return min(quantity, int(math.floor(self.city.gold / 2)))


def get_upgrade_required_resource_quantity(self, building, resource):
    return math.ceil(
        getattr(self.city, building + 'Upgrade' + resource.capitalize()) - getattr(self.city, resource))


def get_food_purchase_quantity_for_reserve(self):
    if self.city.food < self.city.foodReserveMin:
        return min(self.city.foodReserve - self.city.food, math.floor(self.city.gold / 2))
    return 0


async def upgrade_building(self, building):
    if building == "trebuchet":
        await send_message_and_wait(self, self.status.replyMarkup[2])  # Workshop
    else:
        await send_message_and_wait(self, self.status.replyMarkup[1])  # Buildings

    building_index = -1
    for x in range(0, len(self.status.replyMarkup)):
        if building.replace("townhall", "town hall").capitalize() in self.status.replyMarkup[x]:
            building_index = x
            break
    if building_index == -1:
        sys.exit("Building " + building + " seems not to exist.")

    await send_message_and_wait(self, self.status.replyMarkup[building_index])

    oldlevel = getattr(self.city, building)
    await send_message_and_wait(self, self.status.replyMarkup[1])  # Upgrade
    while getattr(self.city, building) == oldlevel:
        self.log.error("Something went wrong with " + building + " upgrade, please investigate.")
        await procrastinate(self)
        await send_message_and_wait(self, self.status.replyMarkup[1])  # Upgrade

    self.log.info(building + " upgraded to level " + str(oldlevel + 1))
    for x in range(0, len(self.status.replyMarkup)):
        if "Hire" in self.status.replyMarkup[x] or "Recruit" in self.status.replyMarkup[x]:
            await send_message_and_wait(self, self.status.replyMarkup[x])
            await employ_at_capacity(self, building, False)
            break

    await send_message_and_wait(self, "⬆️ Up menu")


async def purchase_resource(self, resource, desired_quantity):
    if desired_quantity < 1:
        return 0
    quantity = get_purchasable_resource_quantity(self, desired_quantity)
    if quantity < 1:
        return 0
    await send_message_and_wait(self, "Trade")
    await send_message_and_wait(self, "💰 Buy")
    await send_message_and_wait(self, resource.capitalize())
    await send_message_and_wait(self, str(quantity))
    await send_message_and_wait(self, "⬆️ Up menu")
    return desired_quantity - quantity


async def go_to_recruit(self, already):
    if not already:
        await send_message_and_wait(self, "War")
        await send_message_and_wait(self, "Recruit")
    return True


def wall_needs_repair(self):
    return getattr(self.city, 'wallDurability', 0) < getattr(self.city, 'wallMaxDurability', 0)


def pretty_seconds(number):
    mins, secs = divmod(number, 60)
    hours, mins = divmod(mins, 60)
    days, hours = divmod(hours, 24)
    weeks, days = divmod(days, 7)
    weeks = int(weeks)
    days = int(days)
    hours = int(hours)
    mins = int(mins)
    secs = int(secs)
    result = []
    if weeks:
        result.append("%d weeks" % weeks)
    if days:
        result.append("%d days" % days)
    if hours:
        result.append("%d hours" % hours)
    if mins:
        result.append("%d minutes" % mins)
    if secs:
        result.append("%d seconds" % secs)
    return ", ".join(result)


async def inplacerestart():
    totalscripttime = (datetime.now() - scriptStartTime).total_seconds()
    inwords = pretty_seconds(totalscripttime)
    print('[Runtime] ' + inwords)

    if totalscripttime < 100:
        rand = random.randint(1000, 4000)
        print("Very short runtime; Hope " + pretty_seconds(rand) + " of sleep make it go away.")
        await asyncio.sleep(rand)
    logging.warning("better just restart this coroutine, is that a thing?" )
    os.execv(sys.executable, [sys.executable] + sys.argv)
