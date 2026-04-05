"""One-time setup: authenticate with Telegram and print StringSession.

Usage:
    pip install telethon
    python scripts/setup_session.py

You'll be prompted for your API ID, API hash, phone number, and auth code.
Copy the printed StringSession value into the TELEGRAM_SESSION GitHub secret.
"""

import asyncio

from telethon import TelegramClient
from telethon.sessions import StringSession


async def main():
    api_id = int(input("Enter your Telegram API ID: "))
    api_hash = input("Enter your Telegram API hash: ")

    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.start()

    session_string = client.session.save()
    print("\n" + "=" * 60)
    print("Your StringSession (copy this to TELEGRAM_SESSION secret):")
    print("=" * 60)
    print(session_string)
    print("=" * 60)

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
