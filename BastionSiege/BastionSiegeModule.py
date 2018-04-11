import re
import time


def send_message_and_wait(self, message):
    lastid = self.status['lastMsgID']
    self.send_message(self.entity, message)
    while lastid == self.status['lastMsgID']:
        print("lastMsgId is " + str(self.status['lastMsgID']))
        time.sleep(1)
        pass


def return_to_main(self):
    while self.status['menuDepth'] > 0:
        send_message_and_wait(self, 'Back')


def human_readable_indexes(self, message):
    for i in range(0, len(message.split())):
        self.log(str(i) + ": " + message.split()[i])


def parse_message(self, message):
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
    # Clan War
    elif 'The' in message.split()[0]:
        parse_war_clan_join(self, message)
    else:
        self.log('ERROR: unknown message type!!!')
        human_readable_indexes(self, message)


def parse_profile(self, msg):
    """
    TODO
    This is WAY TOO MANUAL - perhaps need some helper methods?
    """
    self.log('Parsing profile')
    msg = msg.split()

    self.log("should try to get clan out of here...")
    # self.city['governor'] = msg[0]
    # self.city['name'] = msg[1]
    self.city['status'] = msg[3]
    self.city['territory'] = msg[5][:-1]
    # self.city['season'] = msg[7][:-1]
    # self.city['weather'] = msg[9][:-1]
    # self.city['timeHour'] = msg[11][:-1].split(":")[0]
    # self.city['timeMinute'] = msg[11][:-1].split(":")[1]
    # self.city['timeSecond'] = msg[11][:-1].split(":")[2]
    self.city['people'] = msg[13][:-1]
    self.city['soldiers'] = msg[15][:-1]
    self.city['gold'] = msg[17][:-1]
    self.city['wood'] = msg[19][:-1]
    self.city['stone'] = msg[21][:-1]
    self.city['food'] = msg[23][:-1]

    self.status['menuDepth'] = 0


def parse_buildings_profile(self, msg):
    self.log('Parsing buildings profile')

    msg = ''.join(msg.split())
    match = re.search("🏤([0-9]+)⛔", msg)
    print(match)
    print(msg)

    rg = re.search('🏤([0-9]+)([⛔,✅])', msg)
    self.city['townhall'] = rg[1]
    self.city['townhallCanUpgrade'] = False if '⛔' == rg[2] else True

    self.city['storage'] = msg[4][:-2]
    self.city['storageCanUpgrade'] = False if '⛔' == msg[4] else True
    tmp = msg[5][:-1].split("/")
    self.city['storageWorkers'] = tmp[0]
    self.city['storageMaxWorkers'] = tmp[1]

    self.city['houses'] = msg[7][:-2]
    self.city['housesCanUpgrade'] = False if '⛔' in msg[7] else True
    tmp = msg[8][:-1].split("/")
    self.city['people'] = tmp[0]
    self.city['maxPeople'] = tmp[1]

    self.city['farm'] = msg[10][:-2]
    self.city['farmCanUpgrade'] = False if '⛔' in msg[10] else True
    tmp = msg[11][:-1].split("/")
    self.city['farmWorkers'] = tmp[0]
    self.city['maxFarmWorkers'] = tmp[1]

    self.city['sawmill'] = msg[13][:-2]
    self.city['sawmillCanUpgrade'] = False if '⛔' in msg[13] else True
    tmp = msg[14][:-1].split("/")
    self.city['sawmillWorkers'] = tmp[0]
    self.city['sawmillMaxWorkers'] = tmp[1]

    self.city['mine'] = msg[16][:-2]
    self.city['mineCanUpgrade'] = False if '⛔' in msg[16] else True
    tmp = msg[17][:-1].split("/")
    self.city['mineWorkers'] = tmp[0]
    self.city['mineMaxWorkers'] = tmp[1]

    self.city['barracks'] = msg[19][:-2]
    self.city['barracksCanUpgrade'] = False if '⛔' in msg[19] else True
    tmp = msg[20][:-1].split("/")
    self.city['soldiers'] = tmp[0]
    self.city['maxSoldiers'] = tmp[1]

    self.city['walls'] = msg[22][:-2]
    self.city['wallsCanUpgrade'] = False if '⛔' in msg[22] else True
    tmp = msg[23][:-1].split("/")
    self.city['archers'] = tmp[0]
    self.city['maxArchers'] = tmp[1]

    self.status['menuDepth'] = 1


def parse_war_profile(self, msg):
    self.log('Parsing war profile')

    tmp = msg.split("\n")
    pretty_print(tmp)

    for i in range(12, len(tmp)):  # Some wasted execution steps here, don't know if anything can be done about that...
        if 'No attacks' in tmp[i]:
            self.city['cooldownDefense'] = tmp[i].split()[4]
        elif 'Next attack' in msg:
            self.city['cooldownAttack'] = tmp[i].split()[4]
            self.city['cooldownAttackClan'] = tmp[i].split()[4]
        elif 'Next ally attack' in msg:
            self.city['cooldownAttackClan'] = tmp[i].split()[5]
        elif 'Continues' in msg:
            self.city['currentEnemy'] = tmp[i][5]
            self.log('WARN: Enemies with space may not be logged properly')
    self.log(self.city)

    msg = msg.split()

    self.city['wins'] = msg[1][:-1]
    self.city['karma'] = msg[3][:-1]
    self.city['territory'] = msg[5][:-1]
    self.city['wall'] = msg[7].split("/")[0]
    self.city['maxWall'] = msg[7][:-1].split("/")[1]
    self.city['archers'] = msg[8].split("/")[0]
    self.city['maxArchers'] = msg[8][:-1].split("/")[1]
    self.city['trebuchet'] = msg[10].split("/")[0]
    self.city['maxTrebuchet'] = msg[10][:-1].split("/")[1]
    self.city['soldiers'] = msg[11].split("/")[0]
    self.city['maxSoldiers'] = msg[11].split("/")[1].split("⚔")[0]
    self.city['food'] = msg[12][:-1].split("🍖")[0]

    self.status['menuDepth'] = 1


def parse_resource_message(self, msg):
    self.log('Parsing resources')
    msg = msg.split()

    self.city['gold'] = msg[2][:-1]
    self.city['wood'] = msg[4][:-1]
    self.city['stone'] = msg[6][:-1]
    self.city['food'] = msg[8][:-1]
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
    self.city['barracks'] = msg[2]
    self.city['soldiers'] = msg[4].split("/")[0]
    self.city['maxSoldiers'] = msg[4].split("/")[1].split("⚔")[0]
    self.city['barracksRecruitCostGold'] = msg[6].split("💰")[0]
    self.city['barracksRecruitCostFood'] = msg[6].split("💰")[1].split("/")[0][:-1]
    self.city['barracksRecruitCostPeople'] = msg[6].split("/")[1][:-1]
    self.city['gold'] = msg[8][:-1]
    self.city['people'] = msg[10][:-1]
    self.city['barracksUpgradeCost'] = msg[12].split("💰")[0]
    self.city['barracksUpgradeWood'] = msg[13].split("🌲")[0]
    self.city['barracksUpgradeStone'] = msg[14].split("⛏")[0]

    self.log("Need to deal with upgradability")

    self.status['menuDepth'] = 2


def parse_building_farm(self, msg):
    self.log('parse farm message')
    msg = msg.split()
    self.city['farm'] = msg[2]
    self.city['farmWorkers'] = msg[4].split("/")[0]
    self.city['maxFarmWorkers'] = msg[4].split("/")[1][:-1]
    self.city['farmLocalStorage'] = msg[5].split("/")[0]
    #  farmMaxLocalStorage
    self.city['dailyFoodProduction'] = int(msg[6].split("🍖")[0])
    self.city['dailyFoodConsumption'] = int(msg[8].split("🍖")[0])
    self.city['storageWorkers'] = msg[10][:-1]
    #  self.city['']
    #  Hire cost and costPeople
    self.city['gold'] = msg[14][:-1]
    self.city['people'] = msg[16][:-1]
    self.city['farmUpgradeCost'] = msg[18].split("💰")[0]
    self.city['farmUpgradeWood'] = msg[19].split("🌲")[0]
    self.city['farmUpgradeStone'] = msg[20].split("⛏")[0]

    self.status['menuDepth'] = 2


def parse_building_houses(self, msg):
    self.log('parse houses message')
    msg = msg.split()
    self.city['houses'] = msg[2]
    self.city['people'] = msg[4].split("/")[0]
    self.city['maxPeople'] = msg[4].split("/")[1][:-1]
    self.city['dailyPeopleIncrease'] = int(msg[5].split("👥")[0])
    self.city['dailyFoodConsumption'] = int(msg[6].split("🍖")[0])
    self.city['dailyFoodProduction'] = int(msg[8].split("🍖")[0])
    self.city['storageWorkers'] = msg[10][:-1]
    self.city['housesUpgradeCost'] = msg[12].split("💰")[0]
    self.city['housesUpgradeWood'] = msg[13].split("🌲")[0]
    self.city['housesUpgradeStone'] = msg[14].split("⛏")[0]

    self.log("did not deal with upgradeability, might need to")

    self.status['menuDepth'] = 2


def parse_building_mine(self, msg):
    self.log('parse mine message')
    msg = msg.split()

    self.city['mine'] = msg[2]
    self.city['mineWorkers'] = msg[4].split("/")[0]
    self.city['mineMaxWorkers'] = msg[4].split("/")[1][:-1]
    self.city['mineLocalStorage'] = msg[5].split("/")[0]
    # mineMaxLocalStorage
    self.city['dailyStoneProduction'] = int(msg[6].split("👥")[0])
    self.city['storageWorkers'] = msg[8][:-1]
    # Individual cost variable for hiring?
    #
    self.city['gold'] = msg[12][:-1]
    self.city['people'] = msg[14][:-1]
    self.city['mineUpgradeCost'] = msg[16].split("💰")[0]
    self.city['mineUpgradeWood'] = msg[17].split("🌲")[0]
    self.city['mineUpgradeStone'] = msg[18].split("⛏")[0]

    self.status['menuDepth'] = 2


def parse_building_sawmill(self, msg):
    self.log('parse sawmill message')
    msg = msg.split()

    self.city['sawmill'] = msg[2]
    self.city['sawmillWorkers'] = msg[4].split("/")[0]
    self.city['sawmillMaxWorkers'] = msg[4].split("/")[1][:-1]
    self.city['sawmillLocalStorage'] = msg[5].split("/")[0]
    # sawmillMaxLocalStorage
    self.city['dailyWoodProduction'] = int(msg[6].split("🌲")[0])
    self.city['storageWorkers'] = msg[8][:-1]
    # Individual cost variable for hiring?
    #
    self.city['gold'] = msg[12][:-1]
    self.city['people'] = msg[14][:-1]
    self.city['sawmillUpgradeCost'] = msg[16].split("💰")[0]
    self.city['sawmillUpgradeWood'] = msg[17].split("🌲")[0]
    self.city['sawmillUpgradeStone'] = msg[18].split("⛏")[0]

    self.status['menuDepth'] = 2


def parse_building_storage(self, msg):
    self.log(self.city)
    msg = msg.split()

    self.city['storage'] = msg[2]
    self.city['storageWorkers'] = msg[4].split("/")[0]
    self.city['storageMaxWorkers'] = msg[4].split("/")[1][:-1]
    self.city['wood'] = msg[6].split("/")[0]
    self.city['maxWood'] = msg[6].split("/")[1][:-1]
    self.city['stone'] = msg[7].split("/")[0]
    self.city['maxStone'] = msg[7].split("/")[1][:-1]
    self.city['food'] = msg[8].split("/")[0]
    self.city['maxFood'] = msg[8].split("/")[1][:-1]
    # Individual cost variable(s) for hiring?
    #
    self.city['gold'] = msg[12][:-1]
    self.city['people'] = msg[14][:-1]
    self.city['storageFillCost'] = msg[16][:-1]
    self.city['mineUpgradeCost'] = msg[18].split("💰")[0]
    self.city['mineUpgradeWood'] = msg[19].split("🌲")[0]
    self.city['mineUpgradeStone'] = msg[20].split("⛏")[0]

    self.status['menuDepth'] = 2


def parse_building_town_hall(self, msg):
    self.log('parsing town hall message')
    msg = msg.split()

    self.city['townhall'] = msg[3]
    self.city['gold'] = msg[5][:-1]
    self.city['maxGold'] = msg[7][:-1]
    self.city['dailyGoldProduction'] = int(msg[8].split("/")[0][:-1])
    self.city['housesUpgradeCost'] = msg[10].split("💰")[0]
    self.city['housesUpgradeWood'] = msg[11].split("🌲")[0]
    self.city['housesUpgradeStone'] = msg[12].split("⛏")[0]
    # Should deal with upgradeability...

    self.status['menuDepth'] = 2


def parse_building_walls(self, msg):
    self.log('parsing walls')
    msg = msg.split()
    self.city['walls'] = msg[2]
    self.city['archers'] = msg[4].split("/")[0]
    self.city['maxArchers'] = msg[4].split("/")[1][:-1]
    # Individual Recruit cost?
    self.log("This will break if less than 1000 walls...  I so shoulda been using regex this whole time...")
    self.city['wallDurability'] = msg[10].split("y")[1].split("/")[0]
    self.city['wallMaxDurability'] = msg[10].split("y")[1].split("/")[1][:-1]
    self.city['gold'] = msg[12][:-1]
    self.city['people'] = msg[14][:-1]
    self.city['wallsUpgradeCost'] = msg[10].split("💰")[0]
    self.city['wallsUpgradeWood'] = msg[11].split("🌲")[0]
    self.city['wallsUpgradeStone'] = msg[12].split("⛏")[0]

    self.status['menuDepth'] = 2


def parse_war_clan_join(self, msg):
    self.log('parsing join')
    human_readable_indexes(self, msg)


def pretty_print(object):
    for i in range(0, len(object)):
        print(i, object[i])
