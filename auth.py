from main import get_config
from telethon import TelegramClient
from os import environ

configs = get_config()
for config in configs:
    print("starting session '" + config[0] + "'")
    TelegramClient(
        config[0],
        environ['TG_API_ID'],
        environ['TG_API_HASH'],
        proxy=None,
    ).start(config[2])
print("done")
