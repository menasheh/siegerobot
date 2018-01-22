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
        time.sleep(random.randint(1000, 4000) / 1000)  # Integer division?
        pass


def update_gold(self):
    # todo - if population wasn't maximum when gold last updated, need to use some sort of summation...
    timediff = math.floor((time.time() - self.city['goldLastUpdated']) / 60)
    # self.log(("Oldtime was " + str(self.city['goldLastUpdated'])) + ", newtime is " + str(time.time()) +
    #         ", and timediff is " + str(timediff) + ". Daily gold is " + str(self.city['dailyGoldProduction']) + ".")
    self.city['gold'] += timediff * self.city['dailyGoldProduction']
    self.city['goldLastUpdated'] = time.time()


def update_resources(self):
    update_resource(self, "wood")
    update_resource(self, "stone")
    update_resource(self, "food")


def update_resource(self, resource):
    timediff = math.floor((time.time() - self.city[resource + 'LastUpdated']) / 60)
    # self.log(("Oldtime was " + str(self.city['goldLastUpdated'])) + ", newtime is " + str(time.time()) +
    #         ", and timediff is " + str(timediff) + ". Daily gold is " + str(self.city['dailyGoldProduction']) + ".")
    self.city[resource] += timediff * self.city['daily' + resource.capitalize() + 'Production']
    self.city[resource + 'LastUpdated'] = time.time()


def procrastinate():
    rand_time = random.randint(120, random.randint(1200, 1500 + random.randint(0, 1) * 300))
    print("snoozing for " + str(rand_time) + " seconds")
    time.sleep(rand_time)


def develop(self):
    # send_message_and_wait(self, self.status['replyMarkup'][1])  # Buildings
    send_message_and_wait(self, "Buildings")  # Buildings
    send_message_and_wait(self, self.status['replyMarkup'][0])  # Town Hall #TODO - this is just to parse coinrate and upgrade resources. Can calculate both of those with math, in theory.
    send_message_and_wait(self, self.status['replyMarkup'][2])  # Back
    send_message_and_wait(self, self.status['replyMarkup'][2])  # Storage
    send_message_and_wait(self, self.status['replyMarkup'][5])  # Back
    send_message_and_wait(self, self.status['replyMarkup'][1])  # Houses
    send_message_and_wait(self, self.status['replyMarkup'][2])  # Back
    send_message_and_wait(self, self.status['replyMarkup'][5])  # Sawmill
    send_message_and_wait(self, self.status['replyMarkup'][4])  # Back
    send_message_and_wait(self, self.status['replyMarkup'][6])  # Mine
    send_message_and_wait(self, self.status['replyMarkup'][4])  # Back
    send_message_and_wait(self, self.status['replyMarkup'][7])  # Farm
    send_message_and_wait(self, self.status['replyMarkup'][5])  # Up Menu
    send_message_and_wait(self, self.status['replyMarkup'][5])  # Trade
    send_message_and_wait(self, self.status['replyMarkup'][1])  # Buy

    while True:

        while (self.city['maxWood'] > self.city['housesUpgradeWood']) \
                & (self.city['maxStone'] > self.city['housesUpgradeStone']):
            purchase_resources_toward_upgrade(self, 'wood', 'houses')
            purchase_resources_toward_upgrade(self, 'stone', 'houses')
            send_message_and_wait(self, self.status['replyMarkup'][4])  # Up Menu

            waittime = math.ceil((self.city['housesUpgradeCost'] - self.city['gold']) / self.city['dailyGoldProduction'])
            self.log("upgrade of houses will require gold generated from " + str(waittime) + " minutes.")

            time.sleep(60 * (waittime + 1))

            send_message_and_wait(self, self.status['replyMarkup'][1])  # Buildings
            send_message_and_wait(self, self.status['replyMarkup'][1])  # Houses

            oldlevel = self.city['houses']
            send_message_and_wait(self, self.status['replyMarkup'][1])  # Upgrade
            while self.city['houses'] == oldlevel:
                self.log("Something went wrong with houses upgrade, please investigate.")
                procrastinate()
                send_message_and_wait(self, self.status['replyMarkup'][1])  # Upgrade

            send_message_and_wait(self, self.status['replyMarkup'][3])  # Up Menu
            send_message_and_wait(self, self.status['replyMarkup'][5])  # Trade
            send_message_and_wait(self, self.status['replyMarkup'][1])  # Buy

        while (self.city['maxWood'] > self.city['townhallUpgradeWood']) \
                & (self.city['maxStone'] > self.city['townhallUpgradeStone']):
            purchase_resources_toward_upgrade(self, 'wood', 'houses')
            purchase_resources_toward_upgrade(self, 'stone', 'houses')
            send_message_and_wait(self, self.status['replyMarkup'][4])  # Up Menu

            waittime = math.ceil((self.city['townhallUpgradeCost'] - self.city['gold']) / self.city['dailyGoldProduction'])
            self.log("upgrade of townhall will require gold generated from " + str(waittime) + " minutes.")

            time.sleep(60 * (waittime + 1))

            send_message_and_wait(self, self.status['replyMarkup'][1])  # Buildings
            send_message_and_wait(self, self.status['replyMarkup'][0])  # Town Hall

            oldlevel = self.city['townhall']
            send_message_and_wait(self, self.status['replyMarkup'][1])  # Upgrade
            while self.city['townhall'] == oldlevel:
                self.log("Something went wrong with townhall upgrade, please investigate.")
                procrastinate()
                send_message_and_wait(self, self.status['replyMarkup'][1])  # Upgrade

            send_message_and_wait(self, self.status['replyMarkup'][3])  # Up Menu
            send_message_and_wait(self, self.status['replyMarkup'][5])  # Trade
            send_message_and_wait(self, self.status['replyMarkup'][1])  # Buy

        purchase_resources_toward_upgrade(self, 'wood', 'storage')
        purchase_resources_toward_upgrade(self, 'stone', 'storage')

        send_message_and_wait(self, self.status['replyMarkup'][4])  # Up Menu

        waittime = math.ceil(((self.city['storageUpgradeCost'] - self.city['gold']) / self.city['dailyGoldProduction']))
        self.log("upgrade of storage will require gold generated from " + str(waittime) + " minutes.")

        time.sleep(60 * waittime)

        send_message_and_wait(self, self.status['replyMarkup'][1])  # Buildings
        send_message_and_wait(self, self.status['replyMarkup'][2])  # Storage

        oldlevel = self.city['storage']
        send_message_and_wait(self, self.status['replyMarkup'][1])  # Upgrade
        while self.city['storage'] == oldlevel:
            self.log("Something went wrong with storage upgrade, please investigate.")
            procrastinate()
            send_message_and_wait(self, self.status['replyMarkup'][1])  # Upgrade

        send_message_and_wait(self, self.status['replyMarkup'][6])  # Up Menu
        send_message_and_wait(self, self.status['replyMarkup'][5])  # Trade
        send_message_and_wait(self, self.status['replyMarkup'][1])  # Buy


def purchase_resources_toward_upgrade(self, resource, building):
    # Assumes in the trade menu. Bad assumption TODO fix
    send_message_and_wait(self, resource.capitalize())
    goal_quantity_index = building + 'Upgrade' + resource.capitalize()
    while self.city[resource] < self.city[goal_quantity_index]:
        purchase_quantity = min([self.city[goal_quantity_index] - self.city[resource],
                                 # self.city['max' + resource.capitalize] - self.city[resource],
                                 math.floor(self.city['gold'] / 2)])
        send_message_and_wait(self, str(purchase_quantity))  # Not future-proof if price of
        # TODO forecast finish time
        procrastinate()
        update_gold(self)  # update gold
        update_resources(self)
        self.log(self.city['replyMarkup'])
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
    elif '🏘Houses' in message:
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
    elif 'Info' in message.split()[0]:
        parse_war_recruitment_info(self, message)
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

    reg = re.compile(r'(\d+)🎖\D+(\d+)\D+(\d+)\D+(\d+)/(\d+)\D+(\d+)/(\d+)\D+(\d+)/(\d+)\D+(\d+)/(\d+)⚔(⛔️|✅)\D+(\d+)🍖'
                     r'(⛔️|✅)(.+Next attack - (\d+) (min|sec)\.)?(.+Next ally attack - (\d+) (min|sec)\.)?(.+No attacks'
                     r' - (\d+) (min|sec)\.)?(.+Continues the battle with( alliance)? \[?(\W?)]?([\w ]+)(\nAttack: (.+)'
                     r'Defence: (.+))?)?', re.S)
    m = re.search(reg, msg)

    self.city['wins'] = int(m.group(1))
    self.city['karma'] = int(m.group(2))
    self.city['territory'] = int(m.group(3))
    self.city['wall'] = int(m.group(4))
    self.city['maxWall'] = int(m.group(5))
    self.city['archers'] = int(m.group(6))
    self.city['maxArchers'] = int(m.group(7))
    self.city['trebuchetWorkers'] = int(m.group(8))
    self.city['maxTrebuchetWorkers'] = int(m.group(9))
    self.city['soldiers'] = int(m.group(10))
    self.city['maxSoldiers'] = int(m.group(11))
    self.city['food'] = int(m.group(13))
    self.city['canAttack'] = False if '⛔' in m.group(12) + m.group(14) else True
    if m.group(15) is None:
        self.city['cooldownAttack'] = 0
    else:
        self.city['cooldownAttack'] = m.group(16) * (1 if m.group(17) is "sec" else 60)
    if m.group(18) is None:
        self.city['cooldownAttackClan'] = 0
    else:
        self.city['cooldownAttackClan'] = m.group(19) * (1 if m.group(20) is "sec" else 60)
    if m.group(21) is None:
        self.city['cooldownDefense'] = 0
    else:
        self.city['cooldownDefense'] = m.group(22) * (1 if m.group(23) is "sec" else 60)
    self.city['cdLastUpdated'] = time.time()
    if m.group(24) is None:
        self.city['warStatus'] = 'peace'
        self.city['currentEnemyClan'] = ''
        self.city['currentEnemyClanName'] = ''
        self.city['currentEnemyName'] = ''
    else:
        if m.group(25) is None:
            self.city['currentEnemyClan'] = m.group(26)
            self.city['currentEnemyName'] = m.group(27)
        else:
            self.city['currentEnemyClan'] = m.group(26)
            self.city['currentEnemyClanName'] = m.group(27)
            if self.city['governor'] in m.group(29): # TODO regardless if i'm attacking or defending, count attackers and defenders. More useful if other bot receives such messages and sends them on here, to aid in decision of attacking or not.
                self.city['warStatus'] = 'clanAttack'
                self.city['currentClanWarEnemies'] = m.group(30)
                self.city['currentClanWarFriends'] = m.group(29)
            elif self.city['governor'] in m.group(30):
                self.city['warStatus'] = 'clanDefence'
                self.city['currentClanWarEnemies'] = m.group(29)
                self.city['currentClanWarFriends'] = m.group(30)
                # TODO check if I'm first, which would mean I'm the one defending
            else:
                self.log('Could not find self in current clan battle!')

    self.status['menuDepth'] = 1


def parse_war_recruitment_info(self, msg):
    reg = re.compile(r'(\d+)/(\d+)\D+(\d+)/(\d+)\D+(\d+)/(\d+)\D+', re.S)
    m = re.search(reg, msg)

    self.city['soldiers'] = m.group(1)
    self.city['maxSoldiers'] = m.group(2)
    self.city['archers'] = m.group(3)
    self.city['maxArchers'] = m.group(4)
    self.city['trebuchetWorkers'] = m.group(5)
    self.city['maxTrebuchetWorkers'] = m.group(6)

    self.status['menuDepth'] = 2


def parse_resource_message(self, msg):
    self.log('Parsing resources')

    if 'delivered' in msg:
        self.log('resources purchased')
        # match = re.search(r'^(\d+)(.).+', msg, re.M) # Don't actually need this... because we have current values anyway
        # self.city[{'🌲': 'wood', '⛏': 'stone', '🍖': 'food'}[match.group(2)]] += match.group(1)
    if 'no place' in msg:
        self.log('no room for resources we attempted to purchase')  # TODO do something about this to ruin trade loop

    regex = re.compile(r'(\d+).$', re.M)
    regex2 = re.compile(r'(\d+)./')

    m = re.findall(regex, msg)
    m2 = re.findall(regex2, msg)

    self.city['gold'] = int(m[0])
    self.city['goldLastUpdated'] = time.time()
    self.city['wood'] = int(m[1])
    self.city['woodLastUpdated'] = time.time()
    self.city['stone'] = int(m[2])
    self.city['stoneLastUpdated'] = time.time()
    self.city['food'] = int(m[3])
    self.city['foodLastUpdated'] = time.time()
    if len(m) > 4:
        #  Technically speaking I could just hardcode 2 or use a resourcePrice variable...
        self.city['woodPrice'] = int(m2[0]) / int(m[4])
        self.city['stonePrice'] = int(m2[1]) / int(m[5])
        self.city['foodPrice'] = int(m2[2]) / int(m[6])
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
    self.log('parsing building - storage')

    self.log('regex this, please!\n')
    self.log(msg)
    self.log("\n")

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
    self.city['storageFillCost'] = int(msg[16][:-2])
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
    self.city['townhallUpgradeCost'] = int(msg[10].split("💰")[0])
    self.city['townhallUpgradeWood'] = int(msg[11].split("🌲")[0])
    self.city['townhallUpgradeStone'] = int(msg[12].split("⛏")[0])
    # Should deal with upgradeability...

    self.status['menuDepth'] = 2


def parse_building_walls(self, msg):
    self.log('parsing walls')

    reg = re.compile(
        r'(\d+)\D+(\d+)/(\d+)🏹\D+(\d+)💰(\d+)🍖/(\d+)👥\D+\+(\d+)\D+(\d+)/(\d+)\D+(\d+)\D+(\d+)👥.+(Repair|'
        r'Upgrade)\D+(\d+)💰(⛔️|✅)\D+(\d+)🌲(⛔️|✅)\D+(\d+)⛏(⛔️|✅)', re.S)
    m = re.search(reg, msg)

    self.city['walls'] = int(m.group(1))
    self.city['archers'] = int(m.group(2))
    self.city['maxArchers'] = int(m.group(3))
    # Individual Recruit cost? 10, 1, 1 are current values of 4, 5, 6
    self.city['wallAttackBonus'] = int(m.group(7))
    self.city['wallDurability'] = int(m.group(8))
    self.city['wallMaxDurability'] = int(m.group(9))
    self.city['gold'] = int(m.group(10))
    self.city['goldLastUpdated'] = time.time()
    self.city['people'] = int(m.group(11))
    self.city['peopleLastUpdated'] = time.time()
    self.city['wallStatus'] = m.group(12)
    self.city['walls' + self.city['wallStatus'] + 'Cost'] = int(m.group(13))
    self.city['walls' + self.city['wallStatus'] + 'Wood'] = int(m.group(15))
    self.city['walls' + self.city['wallStatus'] + 'Stone'] = int(m.group(17))
    self.city['wallsCanUpgrade'] = False if '⛔' in m.group(14) + m.group(16) + m.group(18) else True

    self.status['menuDepth'] = 2


def parse_war_attacked(self, msg):
    self.log('parse attacked')
    match = re.match(r'.+! \[?(\W?)]?(.+) approaches t.+', msg)
    self.city['attackingClan'] = match.group(1)
    self.city['attackingPlayer'] = match.group(2)
    # TODO - indicate that trade can't happen somewherehowhen?


def parse_war_victory(self, msg):
    self.log('parsing victory - no code yet!')
    print(msg)


def parse_war_defeat(self, msg):
    self.log('parsing defeat')

    reg = re.compile(
        r'with \[?(\W)?]?([\w, ]+) complete. Unfortunately, (.+),.+ lose\. (None|Only (\d+)⚔) of the (\d+)⚔\D+(\d+)💰'
        r'\D+(\d+)🗺')
    m = re.search(reg, msg)

    self.city['lastEnemyClan'] = m.group(1)
    self.city['lastEnemyName'] = m.group(2)
    self.city['governor'] = m.group(3)
    if m.group(5) is not None:
        self.city['soldiers'] = self.city['soldiers'] + int(m.group(5))
    self.city['soldiersInPreviousBattle'] = int(m.group(6))
    self.city['gold'] = self.city['gold'] - int(m.group(7))


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
    self.log(self.city['clanAllyUnderAttack'])
    self.log('If that\'s a name of a city, gezunterheit, delete two log lines. Otherwise shift indexes.')
    # todo get way to attack (inline keyboard)


def pretty_print(object):
    for i in range(0, len(object)):
        print(i, object[i])
