import logging
import asyncio
import sys

from telethon import TelegramClient, events

from entities import MessageBuilder
from pubsub.base import Publisher, Channel
from pubsub.subscribers import BaleSubscriber
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
    client = TelegramClient("sessions/anon", settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
    await client.start(phone=settings.TELEGRAM_PHONE)

    logger.info("Attaching handlers to Telegram client...")
    event = events.NewMessage(chats=settings.get_channels_list())
    client.add_event_handler(handler, event)

    logger.info("Setup finished.")
    logger.info("Waiting for messages...\n\n")
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        logger.info("=" * 60)
        logger.info("Starting service...")
        logger.info(f"Target Channel: {settings.TARGET_TELEGRAM_CHANNEL}")
        logger.info(f"Monitoring Channels: {settings.get_channels_list()}")
        logger.info("=" * 60 + "\n")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nShutdown complete")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)
