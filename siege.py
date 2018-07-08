import traceback
import sys
import BastionSiegeModule as Siege
from datetime import datetime
from getpass import getpass
import os
from os.path import expanduser
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.tl.types import (
    KeyboardButton, KeyboardButtonCallback, UpdatesTg, UpdateNewMessage, UpdateShortMessage, UpdateReadHistoryOutbox,
    UpdateReadHistoryInbox, UpdateMessageID
)
from telethon.utils import get_display_name
# from twilio.rest import Client

scriptStartTime = datetime.now()

# File-based logging
logfile = expanduser("~") + '/.hidden/siege'
logext = '.log'
output = open(logfile + logext, 'a+', 1)
sys.stdout = output
sys.stderr = output


def load_config(path='settings'):
    path = 'config/' + path + '.cfg'
    # Loads the user settings.cfg located under `config/` TODO multiple phone numbers
    result = {}
    with open(path, 'r', encoding='utf-8') as file:
        for line in file:
            value_pair = line.split('=')
            left = value_pair[0].strip()
            right = value_pair[1].strip()
            if right.isnumeric():
                result[left] = int(right)
            else:
                result[left] = right

    return result


# twilio = load_config('twilio')
# twilioclient = Client(twilio['sid'], twilio['token'])


def text(message):
    # twilioclient.api.account.messages.create(body=message, from_=twilio['phone_from'], to=twilio['phone_to'])
    pass


def inplacerestart():
    totalscripttime = (datetime.now() - scriptStartTime).total_seconds()
    mins, secs = divmod(totalscripttime, 60)
    hours, mins = divmod(mins, 60)
    hours = int(hours)
    mins = int(mins)
    secs = int(secs)
    print('[Runtime] ' + str(hours) + ":" + str(mins) + ":" + str(secs))

    text("Restarting after " + str(hours) + " hours, " + str(mins) + " minutes and " + str(int(secs))
         + " seconds of siege.")

    dts = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    # os.renames(logfile + logext, logfile + dts + logext)

    if totalscripttime > 100:
        os.execv(sys.executable, [sys.executable] + sys.argv)


def sprint(string, *args, **kwargs):
    """Safe Print (handle UnicodeEncodeErrors on some terminals)"""
    try:
        print(string, *args, **kwargs)
    except UnicodeEncodeError:
        string = string.encode('utf-8', errors='ignore') \
            .decode('ascii', errors='ignore')
        print(string, *args, **kwargs)


def print_title(title):
    # Clear previous window
    print('\n')
    print('=={}=='.format('=' * len(title)))
    sprint('= {} ='.format(title))
    print('=={}=='.format('=' * len(title)))


class SiegeClient(TelegramClient):
    """Bot for Bastion Siege @BastionSiegeBot """

    BOT_ID = int(252148344)  # Applies to all instances of SiegeClient

    def __init__(self, session_user_id, user_phone, api_id, api_hash, proxy=None):
        print_title('Initialization')
        super().__init__(session_user_id, api_id, api_hash, proxy=proxy)

        self.found_media = set()

        print('Connecting to Telegram servers...')
        if not self.connect():
            print('Initial connection failed. Retrying...')
            if not self.connect():
                print('Could not connect to Telegram servers.')
                return

        # Then, ensure we're authorized and have access
        if not self.is_user_authorized():
            print('First run. Sending code request...')
            self.send_code_request(user_phone)

            self_user = None
            while self_user is None:
                code = input('Enter the code you just received: ')
                try:
                    self_user = self.sign_in(user_phone, code)

                # Two-step verification may be enabled
                except SessionPasswordNeededError:
                    pw = getpass('Two step verification is enabled. '
                                 'Please enter your password: ')

                    self_user = self.sign_in(password=pw)

        self.entity = ""

        class Object:
            pass

        self.city = Object()
        self.city.gold = 0
        self.city.goldLastUpdated = 0
        self.city.wood = 0
        self.city.stone = 0
        self.city.food = 0

        self.status = Object()
        self.status.menuDepth = 3

        self.city.update_times = Object()

    def run(self):
        self.add_update_handler(self.update_handler)

        result = client(ResolveUsernameRequest('BastionSiegeBot'))
        self.entity = result.users[0]

        if get_display_name(self.entity) != "Bastion Siege":
            exit("Wrong Entity!")

        self.log("Loading messages...")
        # TODO 10 in production
        total_count, messages, senders = self.get_message_history(self.entity, limit=2)

        for msg in messages:
            if msg.from_id == self.BOT_ID:
                Siege.parse_message(self, msg.message)
                self.status.lastMsgID = msg.id
                if hasattr(self.status, 'menuDepth'):
                    continue

        self.log("Done.")

        Siege.return_to_main(self)

        """
        From Start to finish Bastion Siege logic...
        
        Or is there a way to put it somewhere else, outside the Client?
        
        """

        self.city.upgradePriorities = ['walls', 'trebuchet', 'barracks', 'houses', 'townhall', 'storage']

        Siege.environment(self)
        Siege.build(self)

    def update_handler(self, update_object):
        if type(update_object) is UpdatesTg:
            for update in update_object.updates:
                if type(update) is UpdateNewMessage:
                    if update.message.from_id == self.BOT_ID:
                        message = update.message.message
                        try:
                            Siege.parse_message(self, message)
                        except Exception as err:
                            print('Unexpected error ({}): {} at\n{}'.format(type(err), err, traceback.format_exc()))

                        markup = []

                        class Object:
                            pass
                        chatbuttons = Object()
                        chatbuttons.id = update.message.id
                        chatbuttons.text = []
                        chatbuttons.data = []
                        for row in update.message.reply_markup.rows:
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
                        else:
                            self.log("No markup or data callback entries. Not updating...")
                        self.status.lastMsgID = update.message.id
                else:
                    if not (isinstance(update, UpdateReadHistoryOutbox) or isinstance(update, UpdateReadHistoryInbox) or
                            isinstance(update, UpdateMessageID)):
                        """"""
                        # self.log("Update is Type: ") todo - updatemessageid? useful? uncomment for this debug trail
                        # self.log(type(update))
        elif type(update_object) is UpdateShortMessage:
            if update_object.user_id == self.BOT_ID:
                Siege.parse_message(self, update_object.message)
            else:
                """"""
                # self.log(update_object)
            self.status.lastMsgID = update_object.id
        else:
            if hasattr(update_object, "message"):
                print("update_object is of type: ", type(update_object))
                print(update_object.message.replace(u'\u200B', ''))
            else:
                """"""    # print("[" + str(type(update_object)) + "has no message]")

    @staticmethod
    def log(msg):
        dts = datetime.now().strftime("[%Y-%m-%d_%H:%M:%S] ")
        print(dts, msg)

    @staticmethod
    def restart(city):
        for attr, value in city.__dict__.iteritems():
            print(attr, value)
        inplacerestart()


# TODO - foreach .cfg file in config folder (?)
config = load_config("settings")

client = SiegeClient(
    session_user_id=str(config.get('session_name', 'anonymous')),
    user_phone=str(config['user_phone']),
    api_id=config['api_id'],
    api_hash=str(config['api_hash'])
)

try:
    client.run()

except Exception as e:
    print('Unexpected error ({}): {} at\n{}'.format(type(e), e, traceback.format_exc()))

finally:
    client.disconnect()
    inplacerestart()
