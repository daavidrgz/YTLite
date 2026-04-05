"""Get decrypted IPA from @eeveedecrypterbot via Telegram."""

import asyncio
import os
import re
import sys

from telethon import TelegramClient
from telethon.sessions import StringSession

BOT_USERNAME = "eeveedecrypterbot"
TIMEOUT = 300  # 5 minutes


def extract_url(text: str) -> str | None:
    """Extract a download URL from message text."""
    # Look for URLs that look like IPA downloads
    urls = re.findall(r"https?://\S+", text)
    for url in urls:
        # Strip trailing punctuation that might be part of markdown
        url = url.rstrip(")")
        if ".ipa" in url.lower():
            return url
    # If no .ipa URL, return any non-telegram URL (could be a CDN link)
    for url in urls:
        url = url.rstrip(")")
        if "t.me" not in url and "telegram" not in url:
            return url
    return None


def extract_button_url(message) -> str | None:
    """Extract download URL from inline keyboard buttons."""
    if not message.reply_markup:
        return None
    if hasattr(message.reply_markup, "rows"):
        for row in message.reply_markup.rows:
            for button in row.buttons:
                if hasattr(button, "url") and button.url:
                    url = button.url
                    if ".ipa" in url.lower() or ("t.me" not in url and "telegram" not in url):
                        return url
    return None


async def main():
    api_id = int(os.environ["TELEGRAM_API_ID"])
    api_hash = os.environ["TELEGRAM_API_HASH"]
    session_str = os.environ["TELEGRAM_SESSION"]
    app_store_url = os.environ["APP_STORE_URL"]

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.start()

    try:
        bot = await client.get_entity(BOT_USERNAME)
        print(f"Sending to @{BOT_USERNAME}: {app_store_url}")
        await client.send_message(bot, app_store_url)

        ipa_url = None
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < TIMEOUT:
            await asyncio.sleep(5)

            # Get recent messages from the bot
            messages = await client.get_messages(bot, limit=5)
            for msg in messages:
                if not msg.out and msg.date.timestamp() > start_time - 10:
                    print(f"Bot message: {msg.text[:200] if msg.text else '(no text)'}")

                    # Check for file attachment (bot sends IPA directly)
                    if msg.document:
                        file_name = None
                        for attr in msg.document.attributes:
                            if hasattr(attr, "file_name"):
                                file_name = attr.file_name
                        if file_name and file_name.endswith(".ipa"):
                            print(f"Bot sent IPA file: {file_name}")
                            path = await client.download_media(msg, file=f"/tmp/{file_name}")
                            print(f"Downloaded to: {path}")
                            # Upload as artifact - the workflow will handle this
                            ipa_url = f"file://{path}"
                            break

                    # Check inline buttons
                    btn_url = extract_button_url(msg)
                    if btn_url:
                        print(f"Found button URL: {btn_url}")
                        ipa_url = btn_url
                        break

                    # Check message text for URL
                    if msg.text:
                        text_url = extract_url(msg.text)
                        if text_url:
                            print(f"Found URL in text: {text_url}")
                            ipa_url = text_url
                            break

            if ipa_url:
                break

        if not ipa_url:
            print("Timed out waiting for IPA from bot", file=sys.stderr)
            sys.exit(1)

        # Set GitHub output
        gh_output = os.environ.get("GITHUB_OUTPUT")
        is_local_file = ipa_url.startswith("file://")

        if is_local_file:
            local_path = ipa_url.replace("file://", "")
            # For file attachments, upload as artifact and set path
            if gh_output:
                with open(gh_output, "a") as f:
                    f.write(f"ipa_path={local_path}\n")
                    f.write("ipa_is_file=true\n")
            print(f"IPA downloaded locally: {local_path}")
        else:
            if gh_output:
                with open(gh_output, "a") as f:
                    f.write(f"ipa_url={ipa_url}\n")
                    f.write("ipa_is_file=false\n")
            print(f"IPA URL: {ipa_url}")

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
