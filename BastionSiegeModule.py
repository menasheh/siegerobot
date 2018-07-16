import math
import random
import re
import sys
import time


def clean_trim(string):
    return ''.join(string.split())


def send_message_and_wait(self, message):
    start_time = time.time()
    lastid = self.status.lastMsgID
    self.send_message(self.entity, message)
    while lastid == self.status.lastMsgID:
        time.sleep(random.randint(1000, 4000) / 1000)
        sleeptime = int(time.time() - start_time)
        if sleeptime > 300:
            self.log("WARN - slept " + pretty_seconds(sleeptime) +
                     " after sending '" + message + "', continuing without confirmation...")
            return
        pass


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


def procrastinate():
    rand_time = random.randint(120, random.randint(1200, 1500 + random.randint(0, 1) * 300))
    print("snoozing for " + pretty_seconds(rand_time) + ".")
    time.sleep(rand_time)


def environment(self):
    return_to_main(self)
    send_message_and_wait(self, "Workshop")  # Workshop
    send_message_and_wait(self, self.status.replyMarkup[1])  # Back
    send_message_and_wait(self, "Buildings")  # Buildings

    self.city.maxGold = 500000 * self.city.townhall
    self.city.dailyGoldProduction = self.city.houses * 10 + self.city.houses * self.city.townhall * 2  # Assumes max pop
    self.city.dailyPeopleIncrease = self.city.houses

    self.city.dailyWoodProduction = self.city.sawmill * 10
    self.city.dailyStoneProduction = self.city.mine * 10
    self.city.dailyFoodProduction = self.city.farm * 10

    structure_exists(self)
    resource_hires(self)

    self.city.maxResource = (self.city.storage * 50 + 1000) * self.city.storage
    self.city.maxWood = self.city.maxStone = self.city.maxFood = self.city.maxResource

    self.city.dailyFoodConsumption = (self.city.houses - min(self.city.farm, self.city.storage)) * 10 \
        if self.city.houses > min(self.city.farm, self.city.storage) else 0
    self.city.foodReserveHours = 8
    self.city.foodReserve = min(self.city.dailyFoodConsumption * self.city.foodReserveHours * 60, self.city.maxFood)
    self.city.foodReserveMin = self.city.foodReserve / 2

    calc_all_upgrade_costs(self)


def structure_exists(self):
    if self.city.storage == 0:
        send_message_and_wait(self, self.status.replyMarkup[2])  # Storage
        send_message_and_wait(self, self.status.replyMarkup[0])  # Build
        send_message_and_wait(self, self.status.replyMarkup[3])  # Hire
        employ_at_capacity(self, "storage")
        send_message_and_wait(self, self.status.replyMarkup[9])  # Back
        send_message_and_wait(self, self.status.replyMarkup[5])  # Back
    if self.city.farm == 0:
        send_message_and_wait(self, self.status.replyMarkup[5])  # Farm
        send_message_and_wait(self, self.status.replyMarkup[0])  # Build
        send_message_and_wait(self, self.status.replyMarkup[2])  # Hire
        employ_at_capacity(self, "farm")  # todo technically could detect active building from message...
        send_message_and_wait(self, self.status.replyMarkup[9])  # Back
        send_message_and_wait(self, self.status.replyMarkup[4])  # Back
    if self.city.sawmill == 0:
        send_message_and_wait(self, self.status.replyMarkup[6])  # Sawmill
        send_message_and_wait(self, self.status.replyMarkup[0])  # Build
        send_message_and_wait(self, self.status.replyMarkup[2])  # Hire
        employ_at_capacity(self, "sawmill")
        send_message_and_wait(self, self.status.replyMarkup[9])  # Back
        send_message_and_wait(self, self.status.replyMarkup[4])  # Back
    if self.city.mine == 0:
        send_message_and_wait(self, self.status.replyMarkup[7])  # Mine
        send_message_and_wait(self, self.status.replyMarkup[0])  # Build
        send_message_and_wait(self, self.status.replyMarkup[2])  # Hire
        employ_at_capacity(self, "mine")
        send_message_and_wait(self, self.status.replyMarkup[9])  # Back
        send_message_and_wait(self, self.status.replyMarkup[4])  # Back


def employ_up_to_capacity(self, building, already):
    workers, max = get_building_employment_vars(self, building)
    missing = 0
    if getattr(self.city, workers) < getattr(self.city, max):
        already = go_to_recruit(self, already)
        send_message_and_wait(self, building.capitalize())
        missing = employ_at_capacity(self, building, False)
        send_message_and_wait(self, 'Back')
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
                self.log("ERR: I don't know how to employ at " + building + ".")


def employ_at_capacity(self, building, wait=True):
    workers, max = get_building_employment_vars(self, building)

    while getattr(self.city, max) > getattr(self.city, workers):
        hirable = min(self.city.people, getattr(self.city, max) - getattr(self.city, workers))
        if hirable > 0:
            send_message_and_wait(self, str(hirable))
        sleeptime = math.ceil(min(getattr(self.city, max) - getattr(self.city, workers),
                                  self.city.maxPeople) / self.city.dailyPeopleIncrease)
        if sleeptime > 0 and wait:
            self.log("Sleeping " + pretty_seconds(60 * sleeptime) + " to get more workers for " + building + ".")
            time.sleep(60 * sleeptime)
            send_message_and_wait(self, str(sleeptime))
        else:
            return getattr(self.city, max) - getattr(self.city, workers)


def resource_hires(self):
    for x in ['storage', 'farm', 'sawmill', 'mine']:
        workers, max = x + 'Workers', x + 'MaxWorkers'
        if getattr(self.city, workers) < getattr(self.city, max):
            send_message_and_wait(self, x.capitalize())
            send_message_and_wait(self, "Hire")
            employ_at_capacity(self, x)
            send_message_and_wait(self, "Back")
            send_message_and_wait(self, "Back")


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


def return_to_main(self):
    if self.status.menuDepth > 0:
        send_message_and_wait(self, 'Up menu')


def human_readable_indexes(self, message):
    for i in range(0, len(message.split())):
        self.log(str(i) + ": " + message.split()[i])


def parse_message(self, message):
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
        parse_resource_message(self, message)
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
        self.status.atWar = True
        self.status.atWarOffense = True
        self.status.atWarDefense = False
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
        self.log('ERROR: unknown message type!!!')
        print(message)


def parse_numbers_from_message(self, msg, numbers):
    t = re.findall(r'(-?\d+)', msg)

    try:
        for i in range(0, len(numbers)):
            setattr(self.city, numbers[i], int(t.pop(0)))
    except IndexError:
        self.log("incorrect numbers? Message:\n" + msg + "\n" + "numbers:\n" + numbers)


def debug_numbers_from_message(self, msg):
    self.log('DEBUG_MSG:')
    self.log(msg)
    t = re.findall(r'(-?\d+)', msg)
    i = 0
    for j in t:
        self.log(str(i) + ": " + j)
        i += 1


def try_regex(self, regex, msg, method):  # todo get method from call stack
    match = re.match(regex, msg)
    if match is None:
        self.log("REGEX ERROR:")
        self.log("\t" + method + " could not parse:\n" + msg + "\n</msg>\n")
        exit(1)
    return match


def parse_profile(self, msg):
    match = try_regex(self, r'(\W+)?(?:{(.+)})?(?:\[(\W)])?([\w ]+).+ory\d+🗺Season(\w+.+)Weather(\w+.+)',
                      clean_trim(msg), "parse_profile")

    parse_numbers_from_message(self, msg, ['territory', 'time.hour', 'time.minute', 'time.second', 'people', 'soldiers',
                                           'gems', 'gold', 'wood', 'stone', 'food'])

    msg = msg.split()
    self.city.statuses = match.group(1) or ""
    self.city.achievements = match.group(2) or ""
    self.city.alliance = match.group(3) or ""
    self.city.governor = match.group(4)
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
    # TODO - make a method for upgradability, then use numbers too. But for now, it works anyway this way.

    upgrades = ['townhall', 'storage', 'houses', 'farm', 'sawmill', 'mine', 'barracks', 'walls']
    numbers = ['townhall', 'storage', 'storageWorkers', 'storageMaxWorkers', 'houses', 'people', 'maxPeople', 'farm',
               'farmWorkers', 'farmMaxWorkers', 'sawmill', 'sawmillWorkers', 'sawmillMaxWorkers', 'mine', 'mineWorkers',
               'mineMaxWorkers', 'barracks', 'soldiers', 'maxSoldiers', 'walls', 'archers', 'maxArchers']

    self.city.townhall = int(match.group(1))
    self.city.townhallCanUpgrade = False if '⛔' in match.group(2) else True
    self.city.storage = int(match.group(3) or 0)
    if self.city.storage > 0:
        self.city.storageCanUpgrade = False if '⛔' in match.group(4) else True
        self.city.storageWorkers = int(match.group(5))
        self.city.storageMaxWorkers = int(match.group(6))
    self.city.houses = int(match.group(7))
    self.city.housesCanUpgrade = False if '⛔' in match.group(8) else True
    self.city.people = int(match.group(9))
    self.city.maxPeople = int(match.group(10))
    self.city.farm = int(match.group(11) or 0)
    if self.city.farm > 0:
        self.city.farmCanUpgrade = False if '⛔' in match.group(12) else True
        self.city.farmWorkers = int(match.group(13))
        self.city.farmMaxWorkers = int(match.group(14))
    self.city.sawmill = int(match.group(15) or 0)
    if self.city.sawmill > 0:
        self.city.sawmillCanUpgrade = False if '⛔' in match.group(16) else True
        self.city.sawmillWorkers = int(match.group(17))
        self.city.sawmillMaxWorkers = int(match.group(18))
    self.city.mine = int(match.group(19) or 0)
    if self.city.mine > 0:
        self.city.mineCanUpgrade = False if '⛔' in match.group(20) else True
        self.city.mineWorkers = int(match.group(21))
        self.city.mineMaxWorkers = int(match.group(22))
    self.city.barracks = int(match.group(23) or 0)
    if self.city.barracks > 0:
        self.city.barracksCanUpgrade = False if '⛔' in match.group(24) else True
        self.city.soldiers = int(match.group(25))
        self.city.maxSoldiers = int(match.group(26))
    self.city.walls = int(match.group(27) or 0)
    if self.city.walls > 0:
        self.city.wallsCanUpgrade = False if '⛔' in match.group(28) else True
        self.city.archers = int(match.group(29))
        self.city.maxArchers = int(match.group(30))

    self.status.menuDepth = 1  # keeps track of back - up might be different


def parse_war_profile(self, msg):
    numbers = [
        'wins', 'karma', 'territory', 'time.hour', 'time.minute', 'time.second', 'wall', 'maxWall', 'archers',
        'maxArchers', 'food',
    ]

    parse_numbers_from_message(self, msg, numbers)

    reg = re.compile(r'(⛔️|✅).+?(⛔️|✅)(?:.+Next attack - (\d+) (min|sec)\.)?(?:.+Next ally attack - (\d+) (min|sec)\.)?'
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
        self.city.cooldownAttack = m.group(3) * (1 if m.group(4) is "sec" else 60)
    if m.group(5) is None:
        self.city.cooldownAttackClan = 0
    else:
        self.city.cooldownAttackClan = m.group(5) * (1 if m.group(6) is "sec" else 60)
    if m.group(7) is None:
        self.city.cooldownDefense = 0
    else:
        self.city.cooldownDefense = m.group(7) * (1 if m.group(8) is "sec" else 60)
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
                self.log("split by commas and count attackers!")
                self.log("check if first => attacking")
            elif self.city.governor in m.group(
                    14):  # defending
                self.city.warStatus = 'clanDefence'
                self.city.currentClanWarEnemies = m.group(29)
                self.city.currentClanWarFriends = m.group(30)
                self.log("split by commas and count defenders!")
                self.log("check if first => defending")
                # TODO More useful if other bot receives such messages and sends them on here, to aid in decision of
                #  attacking or not.
            else:
                self.log("Could not find self %s in current clan battle!" % self.city.governor)

    self.status.menuDepth = 1


def parse_war_recruitment_info(self, msg):
    parse_numbers_from_message(self, msg, ['soliders', 'maxSoldiers', 'archers', 'maxArchers', 'trebuchetWorkers',
                                           'maxTrebuchetWorkers'])
    self.status.menuDepth = 2


def parse_resource_message(self, msg):
    if 'delivered' in msg:
        'resources purchased'
    if 'find money.' in msg:
        self.log('ERROR: not enough money for resources.')
        send_message_and_wait(self, "1")  # Remind script of actual resource amount by purchasing 1
    if 'no place' in msg:
        self.log('no room for resources we attempted to purchase')  # TODO do something about this to ruin trade loop
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
                                           'storageWorkers', 'farmUpgradeGold', 'farmUpgradePeople', 'gold', 'people',
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
    parse_numbers_from_message(self, msg, ['townhall', 'gold', 'maxGold', 'dailyGoldProduction', 'townhallUpgradeCost',
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
    self.log(msg)

    reg = re.compile(r'with (?:{(.+)})?(?:\[(\W)])?([\w ]+) complete')
    m = re.search(reg, msg)

    self.city.lastEnemyStatuses = m.group(1) or ''
    self.city.lastEnemyClan = m.group(2) or ''
    self.city.lastEnemyName = m.group(3)

    m2 = re.search(r'winners (\d+)⚔ (?:of (\d+)⚔)?', msg)
    self.city.lastBattleReturnedSoldiers = int(m2.group(1))
    self.city.lastBattleSentSoldiers = int(m2.group(2) or m2.group(1))

    m3 = re.search(r'(\d+)💰', msg)
    if m3 is None:
        self.city.lastBattleGold = 0
    else:
        self.city.lastBattleGold = int(m3.group(1))

    m4 = re.search('(\d+)🗺', msg)
    if m4 is None:
        self.city.lastBattleTerritory = 0
        self.city.wallNeedsCheck = True
    else:
        self.city.lastBattleTerritory = int(m4.group(1))

    update_gold(self)
    if not hasattr(self.city, "soldiers"):
        self.city.soldiers = 0
    self.city.soldiers = max(self.city.soldiers + self.city.lastBattleReturnedSoldiers, self.city.barracks * 40)
    self.city.gold += self.city.lastBattleGold
    self.city.territory += self.city.lastBattleTerritory

    self.city.warStatus = 'peace'


def parse_war_defeat(self, msg):
    self.log(msg)
    reg = re.compile(r'with 🗡?(?:{(.+)})?(?:\[(\W)])?([\w, ]+) complete. Unfortunately, ([\w ]+),.+ lose\. (None|Only'
                     r' (\d+)⚔) of (\d+)⚔')
    m = re.search(reg, msg)

    self.city.lastEnemyStatuses = m.group(1)
    self.city.lastEnemyClan = m.group(2)
    self.city.lastEnemyName = m.group(3)
    self.city.governor = m.group(4)
    if m.group(6) is not None:
        self.city.soldiers = self.city.soldiers + int(m.group(6))
    self.city.soldiersInPreviousBattle = int(m.group(7))
    update_gold(self)

    m2 = re.search(r'(\d+)💰', msg)
    if m2 is None:
        self.city.lastBattleGold = 0
    else:
        self.city.lastBattleGold = int(m2.group(1))
        self.city.gold = self.city.gold - self.city.lastBattleGold

    m3 = re.search('(\d+)🗺', msg)
    if m3 is None:
        self.city.lastBattleTerritory = 0
    else:
        self.city.wallNeedsCheck = True
        self.city.lastBattleTerritory = int(m3.group(1))

    self.city.warStatus = 'peace'


def parse_war_clan_defeat(self, msg):
    self.log(msg)
    self.log('ERR: not implemented for above message')

    debug_numbers_from_message(self, msg)


def parse_war_clan_join(self, msg):
    self.log('parsing join - needs reg and inline')
    human_readable_indexes(self, msg)

    debug_numbers_from_message(self, msg)


def parse_war_clan_attack(self, msg):
    self.log(msg)

    match = try_regex(self, r'Your ally \W?(?:{.+})?\[(.)](.+) attacked \W?(?:{.+})?\[(.)](.+) from the alliance '
                            r'\[.](.+)! Y.+', msg, 'parse_war_clan_attack')

    self.city.alliance = match.group(1)
    self.city.clanAllyAttacking = match.group(2)
    self.city.clanDefendingAllianceSymbol = match.group(3)
    self.city.clanDefendingPlayer = match.group(4)
    self.city.clanDefendingAllianceName = match.group(5)
    # todo get way to attack (inline keyboard)


def parse_war_clan_defend(self, msg):
    self.log(msg)

    match = try_regex(self, r'Your ally \W?(?:{.+})?\[(.)](.+) was attacked by \W?(?:{.+})?\[(.)](.+) from \[.](.+)! '
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


def build(self):
    while True:
        return_to_main(self)
        if self.city.wallNeedsCheck or wall_needs_repair(self):
            send_message_and_wait(self, "Buildings")
            send_message_and_wait(self, "Walls")
            if wall_needs_repair(self):
                if self.city.wallsCanUpgrade:
                    send_message_and_wait(self, "Repair")
                else:
                    self.log("Can't repair walls.")  # todo - buy items for it
            self.city.wallNeedsCheck = False
        already = False
        missing = 0
        i = 0
        while missing == 0 and i < len(self.city.warbuildings):
            already, missing = employ_up_to_capacity(self, self.city.warbuildings[i], already)
            i += 1
        if already:
            send_message_and_wait(self, "Up menu")

        buildings = self.city.upgradePriorities
        i = 0
        while self.city.maxWood < getattr(self.city, buildings[i] + 'UpgradeWood') or \
                self.city.maxStone < getattr(self.city, buildings[i] + 'UpgradeStone') or \
                self.city.maxGold < getattr(self.city, buildings[i] + 'UpgradeCost'):
            i += 1

        return_to_main(self)
        requiredfood = purchase_resource(self, "food", get_food_purchase_quantity_for_reserve(self))
        requiredwood = purchase_resource(self, "wood",
                                         get_upgrade_required_resource_quantity(self, buildings[i], "wood"))
        requiredstone = purchase_resource(self, "stone",
                                          get_upgrade_required_resource_quantity(self, buildings[i], "stone"))
        requiredgold = getattr(self.city, buildings[i] + 'UpgradeCost') - self.city.gold

        estimatedtime = get_estimated_time_to_resources(self, requiredgold, requiredfood, requiredwood, requiredstone)

        if estimatedtime > 0:
            self.log(
                "Upgrade of " + buildings[i] + " possible in approximately " + pretty_seconds(60 * estimatedtime) + ".")
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
            self.log("With %d storage, %s maxes out at %d and will take ~%s to complete." % (
                self.city.storage, buildings[i], leveldesired, pretty_seconds(60 * estimatedtime)
            ))
            procrastinate()
            update_gold(self)
            update_resources(self)
        else:
            upgrade_building(self, buildings[i])

        while self.city.warStatus is not 'peace':
            pass


def get_estimated_time_to_resources(self, gold, food, wood, stone):
    return max(0, int(math.ceil((gold + 2 * (food + wood + stone)) / self.city.dailyGoldProduction)))


def get_purchasable_resource_quantity(self, quantity):
    return min(quantity, int(math.floor(self.city.gold / 2)))


def get_upgrade_required_resource_quantity(self, building, resource):
    return math.ceil(getattr(self.city, building + 'Upgrade' + resource.capitalize()) - getattr(self.city, resource))


def get_food_purchase_quantity_for_reserve(self):
    if self.city.food < self.city.foodReserveMin:
        return min(self.city.foodReserve - self.city.food, math.floor(self.city.gold / 2))
    return 0


def upgrade_building(self, building):
    if building == "trebuchet":
        send_message_and_wait(self, self.status.replyMarkup[2])  # Workshop
    else:
        send_message_and_wait(self, self.status.replyMarkup[1])  # Buildings

    building_index = -1
    for x in range(0, len(self.status.replyMarkup)):
        if building.replace("townhall", "town hall").capitalize() in self.status.replyMarkup[x]:
            building_index = x
            break
    if building_index == -1:
        sys.exit("Building " + building + " seems not to exist.")

    send_message_and_wait(self, self.status.replyMarkup[building_index])

    oldlevel = getattr(self.city, building)
    send_message_and_wait(self, self.status.replyMarkup[1])  # Upgrade
    while getattr(self.city, building) == oldlevel:
        self.log("Something went wrong with " + building + " upgrade, please investigate.")
        procrastinate()  # TODO - use waittime method, again (in case lost money to war, for example)
        send_message_and_wait(self, self.status.replyMarkup[1])  # Upgrade

    self.log(building + " upgraded to level " + str(oldlevel + 1))
    for x in range(0, len(self.status.replyMarkup)):
        if "Hire" in self.status.replyMarkup[x] or "Recruit" in self.status.replyMarkup[x]:
            send_message_and_wait(self, self.status.replyMarkup[x])
            employ_at_capacity(self, building, False)
            break

    send_message_and_wait(self, "Up menu")


def purchase_resource(self, resource, desired_quantity):
    if desired_quantity < 1:
        return 0
    quantity = get_purchasable_resource_quantity(self, desired_quantity)
    if quantity < 1:
        return 0
    send_message_and_wait(self, "Trade")
    send_message_and_wait(self, "💰 Buy")
    send_message_and_wait(self, resource.capitalize())
    send_message_and_wait(self, str(quantity))
    send_message_and_wait(self, "Up menu")
    return desired_quantity - quantity


def go_to_recruit(self, already):
    if not already:
        send_message_and_wait(self, "War")
        send_message_and_wait(self, "Recruit")
    return True


def wall_needs_repair(self):
    return self.city.wallDurability < self.city.wallMaxDurability


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
