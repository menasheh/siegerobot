from BastionSiege import BastionSiegeModule as Siege
import time
import traceback
from getpass import getpass
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.tl.types import (
    UpdatesTg, UpdateNewMessage, UpdateShortMessage, UpdateReadHistoryOutbox, UpdateReadHistoryInbox, UpdateMessageID
)
from telethon.utils import get_display_name


def load_config(path='settings'):
    path = 'settings/' + path + '.cfg'
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

    BOT_ID = int(252148344)

    status = {'menuDepth': 3}  # TODO Is this properly instanced? Does it belong in init, possibly?
    city = {'gold': 0, 'wood': 0, 'stone': 0, 'food': 0}

    states = {'main', 'war', 'ranking', 'buildings', 'alliance', 'settings.cfg', 'workshop', 'trade',
              'help', 'war.patrol', 'war.patrol', 'war.recruit'
              }

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

    def run(self):
        self.add_update_handler(self.update_handler)

        result = client(ResolveUsernameRequest('BastionSiegeBot'))
        self.entity = result.users[0]

        if get_display_name(self.entity) != "Bastion Siege":
            exit("Wrong Entity!")

        self.log("Loading messages...")
        # TODO 10 in production
        total_count, messages, senders = self.get_message_history(self.entity, limit=20)

        for msg in messages:
            self.log(msg)
            if msg.from_id == self.BOT_ID:
                Siege.parse_message(self, msg.message)
                self.status['lastMsgID'] = msg.id
                if hasattr(self.status, 'menuDepth'):
                    continue

        self.log("Done loading messages...")
        Siege.return_to_main(self)

        """
        From Start to finish Bastion Siege logic...
        
        Or is there a way to put it somewhere else, outside the Client?
        
        """

        # upgradePriorities = {0, 1, 3, 4, 2}

        Siege.develop(self)

    def update_handler(self, update_object):
        if type(update_object) is UpdatesTg:
            for update in update_object.updates:
                if type(update) is UpdateNewMessage:
                    if update.message.from_id == self.BOT_ID:
                        message = update.message.message
                        # for i in range(0, len(message.split())):
                        #    self.log(str(i) + ": " + message.split()[i])
                        Siege.parse_message(self, message)

                        markup = []
                        for row in update.message.reply_markup.rows:
                            for button in row.buttons:
                                markup.append(button.text)
                        if not markup == []:  # TODO Make sure this works - on clan defend, shouldn't change it
                            self.status['replyMarkup'] = markup
                        else:
                            self.log("New markup empty, not updating...")
                        # Siege.pretty_print(markup)  # TEST line
                        self.status['lastMsgID'] = update.message.id
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
            self.status['lastMsgID'] = update_object.id
        else:
            if hasattr(update_object, "message"):
                print("update_object is of type: ", type(update_object))
                print(update_object.message.replace(u'\u200B', ''))
            else:
                """"""    # print("[" + str(type(update_object)) + "has no message]")

    @staticmethod
    def log(msg):
        print(msg)

# TODO - foreach .cfg file in config folder (?)
config = load_config("settings")

client = SiegeClient(
    session_user_id=str(config.get('session_name', 'anonymous')),
    user_phone=str(config['user_phone']),
    api_id=config['api_id'],
    api_hash=str(config['api_hash'])
)

print('Initialization done, but might need to hiccup over prime numbers for a couple seconds...')

try:
    client.run()

except Exception as e:
    print('Unexpected error ({}): {} at\n{}'.format(
        type(e), e, traceback.format_exc()))

finally:
    client.disconnect()
    print('\nThanks for using the bot! Exiting...')  # TODO - time running
