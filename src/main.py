import logging

import asyncio
from telethon import TelegramClient, events

from entities import Message, File, MessageBuilder
from pubsub.base import Publisher, Channel
from pubsub.subscribers import BaleSubscriber, send_file_to_bale
from config import settings

logger = logging.getLogger(__name__)


DEFAULT = "__default__"
publisher = Publisher()


async def handler(event):
    logger.info("New Message Received!")
    logger.info("Building Message object...")

    builder = MessageBuilder()
    message = await builder.build_message_from_telegram_event(event)

    logger.info("Publishing the message...")
    await publisher.publish(DEFAULT, message)


async def main():
    logger.info("Creating channels and subscribers...")
    channel = Channel()
    bale_subscriber = BaleSubscriber()
    publisher.channels[DEFAULT] = channel
    publisher.subscribe(DEFAULT, bale_subscriber)

    logger.info("Creating telegram client...")
    client = TelegramClient("anon", settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
    await client.start(phone=settings.TELEGRAM_PHONE)

    logger.info("Attaching handlers to Telegram client...")
    event = events.NewMessage(chats=settings.get_channels_list())
    client.add_event_handler(handler, event)

    logger.info("Setup finished.")
    logger.info("Waiting for messages...\n\n")
    await client.run_until_disconnected()


async def main2():
    await send_file_to_bale(File(
        id=123,
        name="file_name.txt",
        mime_type="application/text",
        size_in_bytes=23,
        content=b"12345",
    ))

if __name__ == "__main__":
    logger.info("Starting service...\n")
    asyncio.run(main())
