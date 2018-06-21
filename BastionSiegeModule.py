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
        sleeptime = int(time.time() - start_time) / 60
        if sleeptime > 18:
            self.log("WARN - sleeping " + str(int(sleeptime / 60)) + str(sleeptime % 60) + " minutes.  Relaunching...")
            self.restart()
        pass


def update_gold(self):
    # todo - if population wasn't maximum when gold last updated, need to use some sort of summation...
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
    print("snoozing for " + str(rand_time) + " seconds")
    # TODO URGENT TODO - use /refresh and continue when breaks, but save line for a debug breakpoint too somewhere...
    time.sleep(rand_time)


def environment(self):
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
    war_prepare(self)

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


def employ_at_capacity(self, building):
    if building in ['storage', 'farm', 'sawmill', 'mine', 'trebuchet']:
        workers, max = building + 'Workers', building + 'MaxWorkers'
    else:
        if building == 'walls':
            workers, max = 'archers', 'maxArchers'
        else:
            if building == 'barracks':
                workers, max = 'soldiers', 'maxSoldiers'
            else:
                sys.exit("I don't know how to employ at " + building + ".")

    while getattr(self.city, max) > getattr(self.city, workers):
        hirable = min(self.city.people, getattr(self.city, max) - getattr(self.city, workers))
        if hirable > 0:
            send_message_and_wait(self, str(hirable))
        sleeptime = math.ceil(min(getattr(self.city, max) - getattr(self.city, workers),
                                  self.city.maxPeople) / self.city.dailyPeopleIncrease)
        if sleeptime > 0:
            self.log("Sleeping " + str(sleeptime) + " minutes to get more workers for " + building + ".")
            time.sleep(60 * sleeptime)
            send_message_and_wait(self, str(sleeptime))


def resource_hires(self):
    for x in ['storage', 'farm', 'sawmill', 'mine']:
        workers, max = x + 'Workers', x + 'MaxWorkers'
        if getattr(self.city, workers) < getattr(self.city, max):
            send_message_and_wait(self, x.capitalize())
            send_message_and_wait(self, "Hire")
            employ_at_capacity(self, x)
            send_message_and_wait(self, "Back")
            send_message_and_wait(self, "Back")


def war_prepare(self):
    send_message_and_wait(self, "Walls")
    if self.city.wallDurability < self.city.wallMaxDurability:
        if self.city.wallsCanUpgrade:
            send_message_and_wait(self, "Repair")
        else:
            self.log("Can't repair walls.")  # Todo fix by wait
    send_message_and_wait(self, "Up menu")
    send_message_and_wait(self, "War")
    send_message_and_wait(self, "Recruit")

    if self.city.trebuchetWorkers < self.city.maxTrebuchetWorkers:
        send_message_and_wait(self, 'Trebuchet')
        employ_at_capacity(self, 'trebuchet')
        send_message_and_wait(self, 'Back')
    if self.city.archers < self.city.maxArchers:
        send_message_and_wait(self, 'Walls')
        employ_at_capacity(self, 'walls')
        send_message_and_wait(self, 'Back')
    if self.city.soldiers < self.city.maxSoldiers:
        send_message_and_wait(self, 'Barracks')
        employ_at_capacity(self, 'barracks')
        send_message_and_wait(self, 'Back')

    send_message_and_wait(self, "Up menu")


def calc_all_upgrade_costs(self):
    calc_upgrade_costs(self, 'sawmill')
    calc_upgrade_costs(self, 'mine')
    calc_upgrade_costs(self, 'farm')
    calc_upgrade_costs(self, 'houses')
    calc_upgrade_costs(self, 'townhall')
    if hasattr(self.city, "barracks") and (self.city.barracks != 0):
        calc_upgrade_costs(self, 'barracks')
    if hasattr(self.city, "wall") and (self.city.wall != 0):
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


def develop(self):
    environment(self)

    send_message_and_wait(self, self.status.replyMarkup[5])  # Trade
    send_message_and_wait(self, self.status.replyMarkup[1])  # Buy

    while True:
        upgrade_while_possible(self, 'houses')
        upgrade_while_possible(self, 'townhall')
        # upgrade_while_possible(self, 'walls')
        upgrade_while_possible(self, 'storage')


def purchase_resources_toward_upgrade(self, resource, building):
    check_food_reserve(self)
    # Assumes in the trade menu. Bad assumption TODO fix
    send_message_and_wait(self, resource.capitalize())
    goal_quantity_attribute_name = building + 'Upgrade' + resource.capitalize()
    if getattr(self.city, goal_quantity_attribute_name) > getattr(self.city, 'max' + resource.capitalize()):
        self.log("Will attempt to purchase " + str(getattr(self.city, goal_quantity_attribute_name)) + " " + resource +
                 " to upgrade " + building + " but max" + resource.capitalize() + " is " + str(
            getattr(self.city, 'max' +
                    resource.capitalize())))
    while getattr(self.city, resource) < getattr(self.city, goal_quantity_attribute_name):
        purchase_quantity = min(getattr(self.city, goal_quantity_attribute_name) - getattr(self.city, resource),
                                math.floor(self.city.gold / 2))
        send_message_and_wait(self, str(purchase_quantity))  # Not future-proof if price changes
        # TODO forecast finish time
        if self.city.gold < 2:
            procrastinate()
            update_gold(self)  # update gold
            update_resources(self)

    # send_message_and_wait(self, self.status.replyMarkup[9])  # Back # Markup wasn't working b/c clan attacks perhaps
    send_message_and_wait(self, "⬅️ Back")  # Back


def check_food_reserve(self):
    if self.city.food < self.city.foodReserveMin:
        self.log("Daily Food Consumption: " + str(self.city.dailyFoodConsumption))
        self.log("Buying food reserve up to " + str(self.city.foodReserve))
        send_message_and_wait(self, "Food")
        while self.city.food < self.city.foodReserve:
            purchase_quantity = min(self.city.foodReserve - self.city.food,
                                    math.floor(self.city.gold / 2))
            send_message_and_wait(self, str(purchase_quantity))  # Not future-proof if price changes
            if self.city.gold < 2:
                procrastinate()
                update_gold(self)  # update gold
                update_resources(self)
        send_message_and_wait(self, "⬅️ Back")  # Back


def farm(self):
    return_to_main(self)
    send_message_and_wait(self, "Buildings")  # Buildings
    send_message_and_wait(self, self.status.replyMarkup[3])  # Barracks
    send_message_and_wait(self, self.status.replyMarkup[4])  # War

    # If walls need repairing, do it

    # If anyone needs recruiting - barracks, wall, trebuchet, do it
    # Find someone to kill
    # Kill them
    # Wait until army returns - then buy resources toward upgrade


def gold_time_to_upgrade(self, building):
    return max(0, int(
        math.ceil((getattr(self.city, building + 'UpgradeCost') - self.city.gold) / self.city.dailyGoldProduction)))


def upgrade_while_possible(self, building):
    while self.city.maxWood > getattr(self.city, building + 'UpgradeWood') and \
            self.city.maxStone > getattr(self.city, building + 'UpgradeStone'):

        purchase_resources_toward_upgrade(self, 'wood', building)
        purchase_resources_toward_upgrade(self, 'stone', building)
        send_message_and_wait(self, self.status.replyMarkup[4])  # Up Menu

        waittime = gold_time_to_upgrade(self, building)

        if waittime > 0:
            self.log("Upgrade of " + building + " will require gold income from " + str(waittime) + " minutes.")
            time.sleep(60 * (waittime + 1))

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
        index = -1
        for x in range(0, len(self.status.replyMarkup)):
            if "menu" in self.status.replyMarkup[x]:
                index = x
                break
        if index == -1:
            sys.exit("ReplyMarkup appears to miss a menu button.")
        for x in range(0, len(self.status.replyMarkup)):
            if "Hire" in self.status.replyMarkup[x]:
                send_message_and_wait(self, "Hire")
                employ_at_capacity(self, building)
                send_message_and_wait(self, "Back")
                break

        send_message_and_wait(self, self.status.replyMarkup[index])  # Up Menu
        send_message_and_wait(self, self.status.replyMarkup[5])  # Trade
        send_message_and_wait(self, self.status.replyMarkup[1])  # Buy
        if building == "storage":
            break


def return_to_main(self):
    while self.status.menuDepth > 0:
        send_message_and_wait(self, 'Back')


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
    elif 'Wins' in message:
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
    elif 'help defend' in message:
        parse_war_clan_defend(self, message)
    # elif 'The' in message.split()[0]:  # This was probably NOT intended as a catch all...
    #    parse_war_clan_join(self, message)
    elif 'your alliance lose' in message:
        parse_war_clan_defeat(self, message)
    else:
        self.log('ERROR: unknown message type!!!')
        print(message)


def parse_numbers_from_message(self, msg, numbers):
    t = re.findall(r'(\d+)', msg)

    for i in range(0, len(numbers) - 1):
        setattr(self.city, numbers[i], int(t.pop(0)))


def debug_numbers_from_message(self, msg):
    self.log('DEBUG_MSG:')
    self.log(msg)
    t = re.findall(r'(\d+)', msg)
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
    match = try_regex(self, r'\[?(\W?)]?.+y([0-9]+)🗺Season(\w+.+)Weather(\w+.+)Time([0-9]{2}):([0-9]{2}):([0-9]{2})🕓'
                            r'People([0-9]+)👥Army([0-9]+)⚔Gems([0-9]+)💎Gold([0-9]+)💰Wood([0-9]+)🌲Stone([0-9]+)⛏Food(['
                            r'0-9]+)🍖', clean_trim(msg), "parse_profile")

    debug_numbers_from_message(self, msg)

    msg = msg.split()
    self.city.alliance = match.group(1) if len(match.group(1)) > 0 else "none"
    self.city.governor = msg[0] if self.city.alliance is "none" else msg[0][3:]
    self.city.name = msg[1]
    self.city.status = msg[3]
    self.city.territory = int(match.group(2))
    self.city.season = match.group(3)
    self.city.weather = match.group(4)
    self.city.timeHour = match.group(5)
    self.city.timeMinute = match.group(6)
    self.city.timeSecond = match.group(7)
    self.city.people = int(match.group(8))
    self.city.update_times.people = time.time()
    self.city.soldiers = int(match.group(9))
    self.city.gold = int(match.group(10))
    self.city.update_times.gold = time.time()
    self.city.wood = int(match.group(11))
    self.city.update_times.wood = time.time()
    self.city.stone = int(match.group(12))
    self.city.update_times.stone = time.time()
    self.city.food = int(match.group(13))
    self.city.update_times.food = time.time()

    self.status.menuDepth = 0


def parse_buildings_profile(self, msg):
    msg = clean_trim(msg)
    match = try_regex(self,
                      r'.+🏤([0-9]+)([⛔,✅]).?(?:🏚([0-9]+)([⛔,✅])\D?([0-9]+)/([0-9]+)👥)?🏘([0-9]+)([⛔,✅])\D?([0-9]+)/'
                      r'([0-9]+)👥(?:🌻([0-9]+)([⛔,✅])\D?([0-9]+)/([0-9]+)👥)?(?:🌲([0-9]+)([⛔,✅])\D?([0-9]+)/([0-9]+)👥)'
                      r'?(?:⛏([0-9]+)([⛔,✅])\D?([0-9]+)/([0-9]+)👥)?(?:🛡([0-9]+)([⛔,✅])\D?([0-9]+)/([0-9]+)⚔)?(?:🏰(['
                      r'0-9]+)([⛔,✅])\D?([0-9]+)/([0-9]+))?(?:🏹)?.+', msg, "parse_buildings_profile")

    debug_numbers_from_message(self, msg)

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
                self.log('Could not find self in current clan battle!')

    self.status.menuDepth = 1


def parse_war_recruitment_info(self, msg):
    reg = re.compile(r'(\d+)/(\d+)\D+(\d+)/(\d+)\D+(\d+)/(\d+)\D+', re.S)
    m = re.search(reg, msg)

    debug_numbers_from_message(self, msg)

    self.city.soldiers = int(m.group(1))
    self.city.maxSoldiers = int(m.group(2))
    self.city.archers = int(m.group(3))
    self.city.maxArchers = int(m.group(4))
    self.city.trebuchetWorkers = int(m.group(5))
    self.city.maxTrebuchetWorkers = int(m.group(6))

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
    self.log('Parsing scout - needs inline chap')
    msg = msg.split()

    debug_numbers_from_message(self, msg)
    #  m = re.search(r'^Our scouts found (\w+) in his domain (\w+) with')

    tmp = msg.index('domain') + 1
    tmp2 = msg.index('with') - 1
    self.city.enemyDomain = msg[tmp]
    if tmp2 != tmp:
        for i in range(1, tmp2 - tmp):
            self.city.enemyDomain += " " + msg[tmp + i]
    self.city.enemyTerritory = msg[tmp2 + 2][:-1]
    self.city.enemyKarma = msg[tmp2 + 9][:-1]

    self.status.menuDepth = 1


def parse_building_barracks(self, msg):
    parse_numbers_from_message(self, msg, [
        'barracks', 'soldiers', 'maxSoldiers', 'barracksRecruitCostGold', 'barracksRecruitCostFood',
        'barracksRecruitCostPeople', 'gold', 'people', 'barracksUpgradeCost', 'barracksUpgradeWood',
        'barracksUpgradeStone'
    ])

    self.log("dbg-need to parse barracks upgradability")

    self.status.menuDepth = 2


def parse_building_farm(self, msg):
    reg = re.compile(r'-?(\d+)')

    debug_numbers_from_message(self, msg)

    m = re.findall(reg, msg)

    self.city.farm = int(m[0])
    self.city.farmWorkers = int(m[1])
    self.city.farmMaxWorkers = int(m[2])
    self.city.farmLocalStorage = int(m[3])
    #  farmMaxLocalStorage
    self.city.dailyFoodProduction = int(m[5])
    self.city.dailyFoodConsumption = int(m[6])
    self.city.storageWorkers = int(m[7])
    #  Hire cost and costPeople
    self.city.gold = int(m[10])
    self.city.people = int(m[11])
    self.city.farmUpgradeCost = int(m[12])
    self.city.farmUpgradeWood = int(m[13])
    self.city.farmUpgradeStone = int(m[14])

    self.status.menuDepth = 2


def parse_building_houses(self, msg):
    reg = re.compile(r'(\d+)')
    m = re.findall(reg, msg)

    debug_numbers_from_message(self, msg)

    self.city.houses = int(m[0])
    self.city.people = int(m[1])
    self.city.update_times.people = time.time()
    self.city.maxPeople = int(m[2])
    self.city.dailyPeopleIncrease = int(m[3])
    self.city.dailyFoodConsumption = int(m[4])
    self.city.dailyFoodProduction = int(m[5])
    self.city.storageWorkers = int(m[6])
    self.city.housesUpgradeCost = int(m[7])
    self.city.housesUpgradeWood = int(m[8])
    self.city.housesUpgradeStone = int(m[9])

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
    storage_is_full = 1

    reg = re.compile(r'(\d+)')

    debug_numbers_from_message(self, msg)

    m = re.findall(reg, msg)

    self.city.storage = int(m[0])
    self.city.storageWorkers = int(m[1])
    self.city.storageMaxWorkers = int(m[2])
    self.city.wood = int(m[3])
    self.city.update_times.wood = time.time()
    self.city.maxWood = int(m[4])
    self.city.stone = int(m[5])
    self.city.update_times.stone = time.time()
    self.city.maxStone = int(m[6])
    self.city.food = int(m[7])
    self.city.update_times.food = time.time()
    self.city.maxFood = int(m[8])
    # Individual cost variable(s) for hiring?
    #
    self.city.gold = int(m[11])
    self.city.update_times.gold = time.time()
    self.city.people = int(m[12])
    self.city.update_times.people = time.time()
    if re.search(re.compile("Fill", re.M), msg):
        self.city.storageFillCost = int(m[13])
        storage_is_full = 0
    else:
        self.city.storageFillCost = 0
    self.city.storageUpgradeCost = int(m[14 - storage_is_full])
    self.city.storageUpgradeWood = int(m[15 - storage_is_full])
    self.city.storageUpgradeStone = int(m[16 - storage_is_full])

    self.status.menuDepth = 2


def parse_building_town_hall(self, msg):
    reg = re.compile(r'(\d+)')
    m = re.findall(reg, msg)

    debug_numbers_from_message(self, msg)

    self.city.townhall = int(m[0])
    self.city.gold = int(m[1])
    self.city.update_times.gold = time.time()
    self.city.maxGold = int(m[2])
    self.city.dailyGoldProduction = int(m[3])
    self.city.townhallUpgradeCost = int(m[4])
    self.city.townhallUpgradeWood = int(m[5])
    self.city.townhallUpgradeStone = int(m[6])
    # Should deal with upgradeability...

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
    self.log(msg)
    self.log('is clan attack different?')


def parse_war_victory(self, msg):
    self.log('parsing victory, but need better regex (if no terr or coins gained, works?')
    print(msg)

    reg = re.compile(
        r'with (?:\[(\W)])?([\w ]+) complete.+winners (\d+)⚔ (?:of (\d+)⚔)?.+(?:reward is (\d+)💰)(?:\.|, and'
        r' (\d+)🗺 joined)')
    m = re.search(reg, msg)

    self.city.warStatus = 'peace'

    self.city.lastEnemyClan = m.group(1) or ''
    self.city.lastEnemyName = m.group(2)
    self.city.lastBattleReturnedSoldiers = int(m.group(3))
    self.city.lastBattleSentSoldiers = int(m.group(4) or m.group(3))
    self.city.lastBattleGold = int(m.group(5) or 0)
    self.city.lastBattleTerritory = int(m.group(6) or 0)

    update_gold(self)
    self.city.soldiers = max(self.city.soldiers + self.city.lastBattleReturnedSoldiers, self.city.barracks * 40)
    self.city.gold += self.city.lastBattleGold
    self.city.territory += self.city.lastBattleTerritory


def parse_war_defeat(self, msg):
    reg = re.compile(
        r'with \[?(\W)?]?([\w, ]+) complete. Unfortunately, (.+),.+ lose\. (None|Only (\d+)⚔) of the (\d+)⚔\D+(\d+)💰'
        r'\D+(\d+)🗺')
    m = re.search(reg, msg)

    self.city.lastEnemyClan = m.group(1)
    self.city.lastEnemyName = m.group(2)
    self.city.governor = m.group(3)
    if m.group(5) is not None:
        self.city.soldiers = self.city.soldiers + int(m.group(5))
    self.city.soldiersInPreviousBattle = int(m.group(6))
    update_gold(self)
    self.city.gold = self.city.gold - int(m.group(7))


def parse_war_clan_defeat(self, msg):
    self.log(msg)
    self.log('ERR: not implemented for above message')

    debug_numbers_from_message(self, msg)


def parse_war_clan_join(self, msg):
    self.log('parsing join - needs reg and inline')
    human_readable_indexes(msg)

    debug_numbers_from_message(self, msg)


def parse_war_clan_defend(self, msg):
    self.log('parsing clan defend - needs inline')
    self.log(msg)

    match = try_regex(self, r'Your ally (?:{(.+)})? (\W?)\[(.)](.+) was attacked by \[(.)](.+) from \[.](.+)! Y.+', msg,
                      'parse_war_clan_defend')

    self.city.alliance = match.group(2)
    self.city.clanAllyUnderAttack = match.group(3)
    self.city.clanAttackingAllianceSymbol = match.group(4)
    self.city.clanAttackingPlayer = match.group(5)
    self.city.clanAttackingAllianceName = match.group(6)

    # todo get way to attack (inline keyboard)


def pretty_print(objecty):
    for i in range(0, len(objecty)):
        print(i, objecty[i])
