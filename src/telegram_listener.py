import logging
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, RPCError
from config import settings

logger = logging.getLogger(__name__)


async def message_handler(event):
    """Handle incoming messages from monitored channels"""
    try:
        logger.info(f"New message received from chat {event.chat_id}")

        # Forward the message to the target channel
        await event.forward_to(settings.TARGET_TELEGRAM_CHANNEL)

        logger.info(f"Message forwarded successfully to {settings.TARGET_TELEGRAM_CHANNEL}")

    except FloodWaitError as e:
        logger.error(f"Flood wait error: need to wait {e.seconds} seconds")
        raise
    except RPCError as e:
        logger.error(f"Telegram RPC error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in message handler: {e}", exc_info=True)
        raise


async def start_telegram_listener():
    """Start the Telegram listener client"""
    logger.info("Initializing Telegram listener...")

    try:
        # Create Telegram client
        client = TelegramClient(
            "sessions/telegram_listener_session",
            settings.TELEGRAM_API_ID,
            settings.TELEGRAM_API_HASH
        )

        # Start the client with phone authentication
        logger.info("Starting Telegram client...")
        await client.start(phone=settings.TELEGRAM_PHONE)

        # Get channels list from settings
        channels = settings.get_channels_list()
        logger.info(f"Monitoring {len(channels)} channel(s): {channels}")
        logger.info(f"Forwarding to: {settings.TARGET_TELEGRAM_CHANNEL}")

        # Register event handler for new messages
        client.add_event_handler(
            message_handler,
            events.NewMessage(chats=channels)
        )

        logger.info("Telegram listener started successfully")
        logger.info("Waiting for messages...\n")

        # Keep the client running
        await client.run_until_disconnected()

    except KeyboardInterrupt:
        logger.info("Telegram listener stopped by user")
        raise
    except Exception as e:
        logger.error(f"Fatal error in Telegram listener: {e}", exc_info=True)
        raise
    finally:
        if 'client' in locals():
            await client.disconnect()
            logger.info("Telegram client disconnected")
