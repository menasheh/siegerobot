from telethon import TelegramClient
from telethon.errors import PhoneNumberBannedError
from os import environ


async def create(name, number):
        new_client = TelegramClient(
            name,
            environ['TG_API_ID'],
            environ['TG_API_HASH'],
            proxy=None,
        )
        await new_client.connect()
        try:
            await new_client.send_code_request(phone=number, force_sms=True)
        except PhoneNumberBannedError:
            return new_client, True
        return new_client, False


def auth(name, number):
    return TelegramClient(
        f'telegram/sessions/{name}',
        environ['TG_API_ID'],
        environ['TG_API_HASH'],
        proxy=None,
    ).start(number)
