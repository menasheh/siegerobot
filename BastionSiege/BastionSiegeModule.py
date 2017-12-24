import math
import random
import re
import time


def clean_trim(string):
    return ''.join(string.split())


def send_message_and_wait(self, message):
    lastid = self.status['lastMsgID']
    self.send_message(self.entity, message)
    while lastid == self.status['lastMsgID']:
        print("lastMsgId is " + str(self.status['lastMsgID']))
        time.sleep(5)
        pass


def update_gold(self):
    timediff = math.floor((time.time() - self.city['goldLastUpdated']) / 1000) - 1
    self.log(timediff)
    self.city['gold'] += timediff * self.city['dailyGoldProduction']


def procrastinate():
    time.sleep(random.randint(120, random.randint(1200, 1500 + random.randint(0, 1) * 300)))


def purchase_resources_toward_upgrade(self, resource, building):
    # Assumes in the trade menu. Bad assumption TODO fix
    send_message_and_wait(self, resource.capitalize())
    goal_quantity_index = building + 'Upgrade' + resource.capitalize()
    while self.city[resource] < self.city[goal_quantity_index]:
        purchase_quantity = min([self.city[goal_quantity_index] - self.city[resource],
                                 # self.city['max' + resource.capitalize] - self.city[resource],
                                 math.floor(self.city['gold'] / 200)])
        print(self.city[goal_quantity_index], self.city[resource], purchase_quantity, math.floor(self.city['gold'] / 200))
        send_message_and_wait(self, str(purchase_quantity))  # Not future-proof if price of
        procrastinate()
        update_gold(self)  # update gold TODO and resources for that amount of time
    send_message_and_wait(self, self.status['replyMarkup'][9])  # Back


def return_to_main(self):
    while self.status['menuDepth'] > 0:
        send_message_and_wait(self, 'Back')


def human_readable_indexes(self, message):
    for i in range(0, len(message.split())):
        self.log(str(i) + ": " + message.split()[i])


def parse_message(self, message):
    message = message.replace(u'\u200B', '')
    # Main Info and Buildings
    if 'Season' in message:
        parse_profile(self, message)
    elif 'Buildings' in message:
        parse_buildings_profile(self, message)
    elif 'Wins' in message:
        parse_war_profile(self, message)
    elif 'Town hall' in message:
        parse_building_town_hall(self, message)
    elif 'Houses' in message:
        parse_building_houses(self, message)
    elif 'Resources' in message.split()[0]:
        parse_resource_message(self, message)
    elif 'Storage' in message.split()[0]:
        parse_building_storage(self, message)
    elif 'Barracks' in message.split()[0]:
        parse_building_barracks(self, message)
    elif 'Walls' in message.split()[0]:
        human_readable_indexes(self, message)
        parse_building_walls(self, message)
    elif 'Sawmill' in message.split()[0]:
        parse_building_sawmill(self, message)
    elif 'Mine' in message.split()[0]:
        parse_building_mine(self, message)
    elif 'Farm' in message.split()[0]:
        parse_building_farm(self, message)
    # War
    elif 'Our scouts' in message:
        parse_scout_message(self, message)
    elif 'Choose number.' in message:
        self.status['expects'] = 'chooseNumber'
    elif 'Siege has started!' in message:
        self.status['atWar'] = True
        self.status['atWarOffense'] = True
        self.status['atWarDefense'] = False
    elif 'Congratulations' in message and 'army' in message:  # remove army part once alliance parser made
        # if 'army' in message:
        parse_war_victory(self, message)
        # elif 'alliance' in message:
        #   parse_war_clan_victory(self, message)
    # Clan War
    elif 'help defend' in message:
        parse_war_clan_defend(self, message)
    # elif 'The' in message.split()[0]:  # This was probably NOT intended as a catch all...
    #    parse_war_clan_join(self, message)
    else:
        self.log('ERROR: unknown message type!!!')
        human_readable_indexes(self, message)
        print(clean_trim(message))
        print(message)


def parse_profile(self, msg):
    self.log('Parsing profile')
    match = re.match(r'\[?(\W?)]?.+y([0-9]+)🗺Season(\w+.+)Weather(\w+.+)Time([0-9]{2}):([0-9]{2}):([0-9]{2})🕓People(['
                     r'0-9]+)👥Army([0-9]+)⚔Gold([0-9]+)💰Wood([0-9]+)🌲Stone([0-9]+)⛏Food([0-9]+)🍖', clean_trim(msg))
    if match is None:
        self.log("Regex Error - Buildings Profile could not parse:\n" + clean_trim(msg) + "\n===END=MSG===\n")
        exit(1)
    msg = msg.split()
    self.city['alliance'] = match.group(1) if len(match.group(1)) > 0 else "none"
    self.city['governor'] = msg[0] if self.city['alliance'] is "none" else msg[0][3:]
    self.city['name'] = msg[1]
    self.city['status'] = msg[3]
    self.city['territory'] = int(match.group(2))
    self.city['season'] = match.group(3)
    self.city['weather'] = match.group(4)
    self.city['timeHour'] = match.group(5)
    self.city['timeMinute'] = match.group(6)
    self.city['timeSecond'] = match.group(7)
    self.city['people'] = int(match.group(8))
    self.city['peopleLastUpdated'] = time.time()
    self.city['soldiers'] = int(match.group(9))
    self.city['gold'] = int(match.group(10))
    self.city['goldLastUpdated'] = time.time()
    self.city['wood'] = int(match.group(11))
    self.city['woodLastUpdated'] = time.time()
    self.city['stone'] = int(match.group(12))
    self.city['stoneLastUpdated'] = time.time()
    self.city['food'] = int(match.group(13))
    self.city['foodLastUpdated'] = time.time()

    self.status['menuDepth'] = 0


def parse_buildings_profile(self, msg):
    self.log('Parsing buildings profile')
    msg = clean_trim(msg)
    match = re.match(r'.+🏤([0-9]+)([⛔,✅]).?🏚([0-9]+)([⛔,✅]).?([0-9]+)/([0-9]+)👥🏘([0-9]+)([⛔,✅]).?([0-9]+)/([0-9]+'
                     r')👥🌻([0-9]+)([⛔,✅]).?([0-9]+)/([0-9]+)👥🌲([0-9]+)([⛔,✅]).?([0-9]+)/([0-9]+)👥⛏([0-9]+)([⛔,✅])'
                     r'.?([0-9]+)/([0-9]+)👥🛡([0-9]+)([⛔,✅]).?([0-9]+)/([0-9]+)⚔🏰([0-9]+)([⛔,✅]).?([0-9]+)/([0-9]+)🏹'
                     r'.+', msg)
    if match is None:
        self.log("Regex Error - Buildings Profile could not parse:\n" + msg + "\n===END=MSG===\n")
        exit(1)

    self.city['townhall'] = int(match.group(1))
    self.city['townhallCanUpgrade'] = False if '⛔' in match.group(2) else True
    self.city['storage'] = int(match.group(3))
    self.city['storageCanUpgrade'] = False if '⛔' in match.group(4) else True
    self.city['storageWorkers'] = int(match.group(5))
    self.city['storageMaxWorkers'] = int(match.group(6))
    self.city['houses'] = int(match.group(7))
    self.city['housesCanUpgrade'] = False if '⛔' in match.group(8) else True
    self.city['people'] = int(match.group(9))
    self.city['maxPeople'] = int(match.group(10))
    self.city['farm'] = int(match.group(11))
    self.city['farmCanUpgrade'] = False if '⛔' in match.group(12) else True
    self.city['farmWorkers'] = int(match.group(13))
    self.city['maxFarmWorkers'] = int(match.group(14))
    self.city['sawmill'] = int(match.group(15))
    self.city['sawmillCanUpgrade'] = False if '⛔' in match.group(16) else True
    self.city['sawmillWorkers'] = int(match.group(17))
    self.city['sawmillMaxWorkers'] = int(match.group(18))
    self.city['mine'] = int(match.group(19))
    self.city['mineCanUpgrade'] = False if '⛔' in match.group(20) else True
    self.city['mineWorkers'] = int(match.group(21))
    self.city['mineMaxWorkers'] = int(match.group(22))
    self.city['barracks'] = int(match.group(23))
    self.city['barracksCanUpgrade'] = False if '⛔' in match.group(24) else True
    self.city['soldiers'] = int(match.group(25))
    self.city['maxSoldiers'] = int(match.group(26))
    self.city['walls'] = int(match.group(27))
    self.city['wallsCanUpgrade'] = False if '⛔' in match.group(28) else True
    self.city['archers'] = int(match.group(29))
    self.city['maxArchers'] = int(match.group(30))

    self.status['menuDepth'] = 1  # keeps track of back - up might be different


def parse_war_profile(self, msg):
    self.log('Parsing war profile')

    tmp = msg.split("\n")
    pretty_print(tmp)

    self.city['cooldownDefense'] = 0
    self.city['cooldownAttack'] = 0
    self.city['cooldownAttackClan'] = 0
    self.city['cdLastUpdated'] = time.time()

    for i in range(12, len(tmp)):  # Some wasted execution steps here, don't know if anything can be done about that...
        if 'No attacks' in tmp[i]:
            self.city['cooldownDefense'] = int(tmp[i].split()[4])
        elif 'Next attack' in msg:
            self.city['cooldownAttack'] = int(tmp[i].split()[4])
            self.city['cooldownAttackClan'] = int(tmp[i].split()[4])
        elif 'Next ally attack' in msg:
            self.city['cooldownAttackClan'] = int(tmp[i].split()[5])
        elif 'Continues' in msg:
            self.city['currentEnemy'] = tmp[i][5]
            self.log('WARN: Enemies with space may not be logged properly')  # TODO regex fix this...

    self.log(self.city)

    msg = msg.split()

    self.city['wins'] = int(msg[1][:-1])
    self.city['karma'] = int(msg[3][:-1])
    self.city['territory'] = int(msg[5][:-1])
    self.city['wall'] = int(msg[7].split("/")[0])
    self.city['maxWall'] = int(msg[7][:-1].split("/")[1])
    self.city['archers'] = int(msg[8].split("/")[0])
    self.city['maxArchers'] = int(msg[8][:-1].split("/")[1])
    self.city['trebuchet'] = int(msg[10].split("/")[0])
    self.city['maxTrebuchet'] = int(msg[10][:-1].split("/")[1])
    self.city['soldiers'] = int(msg[11].split("/")[0])
    self.city['maxSoldiers'] = int(msg[11].split("/")[1].split("⚔")[0])
    self.city['food'] = int(msg[12][:-1].split("🍖")[0])

    self.status['menuDepth'] = 1


def parse_resource_message(self, msg):
    self.log('Parsing resources')

    if 'delivered' in msg:
        self.log('resources purchased')
        # match = re.search(r'^(\d+)(.).+', msg, re.M) # Don't actually need this... because we have current values anyway
        # self.city[{'🌲': 'wood', '⛏': 'stone', '🍖': 'food'}[match.group(2)]] += match.group(1)
    if 'no place' in msg:
        self.log('no room for resources we attempted to purchase')  # TODO do something about this to ruin trade loop

    msg = msg.split()

    self.city['gold'] = int(msg[2][:-1])
    self.city['goldLastUpdated'] = time.time()
    self.city['wood'] = int(msg[4][:-1])
    self.city['woodLastUpdated'] = time.time()
    self.city['stone'] = int(msg[6][:-1])
    self.city['stoneLastUpdated'] = time.time()
    self.city['food'] = int(msg[8][:-1])
    self.city['foodLastUpdated'] = time.time()
    if len(msg) > 10:
        #  Technically speaking I could just hardcode 2 or use a resourcePrice variable...
        self.city['woodPrice'] = int(msg[11].split("💰")[0]) / int(msg[11].split("/")[1][:-1])
        self.city['stonePrice'] = int(msg[13].split("💰")[0]) / int(msg[13].split("/")[1][:-1])
        self.city['foodPrice'] = int(msg[15].split("💰")[0]) / int(msg[15].split("/")[1][:-1])

    self.status['menuDepth'] = 1


def parse_scout_message(self, msg):
    self.log('Parsing scout')
    msg = msg.split()

    #  m = re.search(r'^Our scouts found (\w+) in his domain (\w+) with')

    tmp = msg.index('domain') + 1
    tmp2 = msg.index('with') - 1
    self.city['enemyDomain'] = msg[tmp]
    if tmp2 != tmp:
        for i in range(1, tmp2 - tmp):
            self.city['enemyDomain'] += " " + msg[tmp + i]
    self.city['enemyTerritory'] = msg[tmp2 + 2][:-1]
    self.city['enemyKarma'] = msg[tmp2 + 9][:-1]

    self.status['menuDepth'] = 1


def parse_building_barracks(self, msg):
    self.log('parse barracks message')
    msg = msg.split()
    self.city['barracks'] = int(msg[2])
    self.city['soldiers'] = int(msg[4].split("/")[0])
    self.city['maxSoldiers'] = int(msg[4].split("/")[1].split("⚔")[0])
    self.city['barracksRecruitCostGold'] = int(msg[6].split("💰")[0])
    self.city['barracksRecruitCostFood'] = int(msg[6].split("💰")[1].split("/")[0][:-1])
    self.city['barracksRecruitCostPeople'] = int(msg[6].split("/")[1][:-1])
    self.city['gold'] = int(msg[8][:-1])
    self.city['people'] = int(msg[10][:-1])
    self.city['barracksUpgradeCost'] = int(msg[12].split("💰")[0])
    self.city['barracksUpgradeWood'] = int(msg[13].split("🌲")[0])
    self.city['barracksUpgradeStone'] = int(msg[14].split("⛏")[0])

    self.log("Need to deal with upgradability")

    self.status['menuDepth'] = 2


def parse_building_farm(self, msg):
    self.log('parse farm message')
    msg = msg.split()
    self.city['farm'] = int(msg[2])
    self.city['farmWorkers'] = int(msg[4].split("/")[0])
    self.city['maxFarmWorkers'] = int(msg[4].split("/")[1][:-1])
    self.city['farmLocalStorage'] = int(msg[5].split("/")[0])
    #  farmMaxLocalStorage
    self.city['dailyFoodProduction'] = int(msg[6].split("🍖")[0])
    self.city['dailyFoodConsumption'] = int(msg[8].split("🍖")[0])
    self.city['storageWorkers'] = int(msg[10][:-1])
    #  self.city['']
    #  Hire cost and costPeople
    self.city['gold'] = int(msg[14][:-1])
    self.city['people'] = int(msg[16][:-1])
    self.city['farmUpgradeCost'] = int(msg[18].split("💰")[0])
    self.city['farmUpgradeWood'] = int(msg[19].split("🌲")[0])
    self.city['farmUpgradeStone'] = int(msg[20].split("⛏")[0])

    self.status['menuDepth'] = 2


def parse_building_houses(self, msg):
    self.log('parse houses message')
    msg = msg.split()
    self.city['houses'] = int(msg[2])
    self.city['people'] = int(msg[4].split("/")[0])
    self.city['peopleLastUpdated'] = time.time()
    self.city['maxPeople'] = int(msg[4].split("/")[1][:-1])
    self.city['dailyPeopleIncrease'] = int(msg[5].split("👥")[0])
    self.city['dailyFoodConsumption'] = int(msg[6].split("🍖")[0])
    self.city['dailyFoodProduction'] = int(msg[8].split("🍖")[0])
    self.city['storageWorkers'] = int(msg[10][:-1])
    self.city['housesUpgradeCost'] = int(msg[12].split("💰")[0])
    self.city['housesUpgradeWood'] = int(msg[13].split("🌲")[0])
    self.city['housesUpgradeStone'] = int(msg[14].split("⛏")[0])

    self.log("did not deal with upgradeability, might need to")

    self.status['menuDepth'] = 2


def parse_building_mine(self, msg):
    self.log('parse mine message')
    msg = msg.split()

    self.city['mine'] = int(msg[2])
    self.city['mineWorkers'] = int(msg[4].split("/")[0])
    self.city['mineMaxWorkers'] = int(msg[4].split("/")[1][:-1])
    self.city['mineLocalStorage'] = int(msg[5].split("/")[0])
    # mineMaxLocalStorage
    self.city['dailyStoneProduction'] = int(msg[6].split("⛏")[0])
    self.city['storageWorkers'] = int(msg[8][:-1])
    # Individual cost variable for hiring?
    #
    self.city['gold'] = int(msg[12][:-1])
    self.city['goldLastUpdated'] = time.time()
    self.city['people'] = int(msg[14][:-1])
    self.city['peopleLastUpdated'] = time.time()
    self.city['mineUpgradeCost'] = int(msg[16].split("💰")[0])
    self.city['mineUpgradeWood'] = int(msg[17].split("🌲")[0])
    self.city['mineUpgradeStone'] = int(msg[18].split("⛏")[0])

    self.status['menuDepth'] = 2


def parse_building_sawmill(self, msg):
    self.log('parse sawmill message')
    msg = msg.split()

    self.city['sawmill'] = int(msg[2])
    self.city['sawmillWorkers'] = int(msg[4].split("/")[0])
    self.city['sawmillMaxWorkers'] = int(msg[4].split("/")[1][:-1])
    self.city['sawmillLocalStorage'] = int(msg[5].split("/")[0])
    # sawmillMaxLocalStorage
    self.city['dailyWoodProduction'] = int(msg[6].split("🌲")[0])
    self.city['storageWorkers'] = int(msg[8][:-1])
    # Individual cost variable for hiring?
    #
    self.city['gold'] = int(msg[12][:-1])
    self.city['goldLastUpdated'] = time.time()
    self.city['people'] = int(msg[14][:-1])
    self.city['peopleLastUpdated'] = time.time()
    self.city['sawmillUpgradeCost'] = int(msg[16].split("💰")[0])
    self.city['sawmillUpgradeWood'] = int(msg[17].split("🌲")[0])
    self.city['sawmillUpgradeStone'] = int(msg[18].split("⛏")[0])

    self.status['menuDepth'] = 2


def parse_building_storage(self, msg):
    self.log(self.city)
    msg = msg.split()

    self.city['storage'] = int(msg[2])
    self.city['storageWorkers'] = int(msg[4].split("/")[0])
    self.city['storageMaxWorkers'] = int(msg[4].split("/")[1][:-1])
    self.city['wood'] = int(msg[6].split("/")[0])
    self.city['woodLastUpdated'] = time.time()
    self.city['maxWood'] = int(msg[6].split("/")[1][:-1])
    self.city['stone'] = int(msg[7].split("/")[0])
    self.city['stoneLastUpdated'] = time.time()
    self.city['maxStone'] = int(msg[7].split("/")[1][:-1])
    self.city['food'] = int(msg[8].split("/")[0])
    self.city['foodLastUpdated'] = time.time()
    self.city['maxFood'] = int(msg[8].split("/")[1][:-1])
    # Individual cost variable(s) for hiring?
    #
    self.city['gold'] = int(msg[12][:-1])
    self.city['goldLastUpdated'] = time.time()
    self.city['people'] = int(msg[14][:-1])
    self.city['peopleLastUpdated'] = time.time()
    self.city['storageFillCost'] = int(msg[16][:-1])
    self.city['storageUpgradeCost'] = int(msg[18].split("💰")[0])
    self.city['storageUpgradeWood'] = int(msg[19].split("🌲")[0])
    self.city['storageUpgradeStone'] = int(msg[20].split("⛏")[0])

    self.status['menuDepth'] = 2


def parse_building_town_hall(self, msg):
    self.log('parsing town hall message')
    msg = msg.split()

    self.city['townhall'] = int(msg[3])
    self.city['gold'] = int(msg[5][:-1])
    self.city['goldLastUpdated'] = time.time()
    self.city['maxGold'] = int(msg[7][:-1])
    self.city['dailyGoldProduction'] = int(msg[8].split("/")[0][:-1])
    self.city['housesUpgradeCost'] = int(msg[10].split("💰")[0])
    self.city['housesUpgradeWood'] = int(msg[11].split("🌲")[0])
    self.city['housesUpgradeStone'] = int(msg[12].split("⛏")[0])
    # Should deal with upgradeability...

    self.status['menuDepth'] = 2


def parse_building_walls(self, msg):
    self.log('parsing walls')
    msg = msg.split()
    self.city['walls'] = int(msg[2])
    self.city['archers'] = int(msg[4].split("/")[0])
    self.city['maxArchers'] = int(msg[4].split("/")[1][:-1])
    # Individual Recruit cost?
    self.log("This will break if less than 1000 walls...  I so shoulda been using regex this whole time...") # TODO REGEX THIS
    self.city['wallDurability'] = int(msg[10].split("y")[1].split("/")[0])
    self.city['wallMaxDurability'] = int(msg[10].split("y")[1].split("/")[1][:-1])
    self.city['gold'] = int(msg[12][:-1])
    self.city['goldLastUpdated'] = time.time()
    self.city['people'] = int(msg[14][:-1])
    self.city['peopleLastUpdated'] = time.time()
    self.city['wallsUpgradeCost'] = int(msg[10].split("💰")[0])
    self.city['wallsUpgradeWood'] = int(msg[11].split("🌲")[0])
    self.city['wallsUpgradeStone'] = int(msg[12].split("⛏")[0])

    self.status['menuDepth'] = 2


def parse_war_attacked(self, msg):
    self.log('parse attacked')
    match = re.match(r'.+! \[?(\W?)]?(.+) approaches t.+', msg)
    self.city['attackingClan'] = match.group(1)
    self.city['attackingPlayer'] = match.group(2)
    # TODO - indicate that trade can't happen somewherehowhen?


def parse_war_victory(self, msg):
    self.log('parsing victory - no code yet!')
    print(clean_trim(msg))
    msg = msg.split()


def parse_war_defeat(self, msg):
    self.log('parsing defeat')
    print(clean_trim(msg))


def parse_war_clan_join(self, msg):
    self.log('parsing join')
    human_readable_indexes(msg)


def parse_war_clan_defend(self, msg):
    self.log('parsing clan defend')

    match = re.match(r'Your ally (\W?)\[(.)](.+) was attacked by \[(.)](.+) from \[.](.+)! Y.+', msg)
    if match is None:
        self.log("Regex Error - Clan Defense could not parse:\n" + clean_trim(msg) + "\n===END=MSG===\n")
        return

    self.city['alliance'] = match.group(1)
    self.city['clanAllyUnderAttack'] = match.group(2)
    self.city['clanAttackingAllianceSymbol'] = match.group(3)
    self.city['clanAttackingPlayer'] = match.group(4)
    self.city['clanAttackingAllianceName'] = match.group(5)


def pretty_print(object):
    for i in range(0, len(object)):
        print(i, object[i])
