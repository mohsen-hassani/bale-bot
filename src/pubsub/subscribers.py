import json
import lzma
import logging
from dataclasses import asdict

import aiohttp
from bale import InputFile

from cryptography.fernet import Fernet
from bale.bot import Bot

from config import settings
from entities import Message, File, MAX_FILE_SIZE

logger = logging.getLogger(__name__)

CHUNK_SIZE = 2000


class BaleSubscriber:
    def __init__(self):
        logger.info("Building cipher...")
        self.cipher = Fernet(settings.get_fernet_key_bytes())

    async def __call__(self, message: Message):
        logger.info("Serializing...")
        raw_message = json.dumps(
            {
                "payload": message.body,
                "username": message.source_channel_username,
                "id": message.source_channel_id,
                "buttons": [asdict(b) for b in message.buttons],
                "entities": message.links,
            }
        )
        logger.info("Encrypting...")
        encrypted_message = self.encrypt_message(raw_message)
        logger.info("Sending to Bale...")
        await send_message_to_bale(encrypted_message)

        if message.file:
            logger.info("Message has document")
            await send_file_to_bale(message.file)

        if message.photo:
            logger.info("Message has photo")
            await send_file_to_bale(message.photo)

        logger.info("Done!\n\n")


    def encrypt_message(self, raw_message: str):
        compressed = lzma.compress(raw_message.encode('utf-8'))
        encrypted = self.cipher.encrypt(compressed)
        return encrypted.decode()


async def send_message_to_bale(message: str) -> None:
    url = f"https://tapi.bale.ai/bot{settings.BALE_TOKEN}/sendMessage"
    chunks = _get_message_chunks(message)

    for index, chunk in enumerate(chunks):
        msg = chunk + f"\n\n======== PART {index + 1} OF {len(chunks)} ========"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"chat_id": settings.BALE_TARGET_CHAT_ID, "text": msg}) as response:
                status_code = response.status
                if status_code != 200:
                    text = await response.text()
                    logger.warning(f"Could not send request to Bale due to this error ({status_code}): {text}")
                logger.info("Message sent successfully!")


async def send_file_to_bale(file: File) -> None:
    if file.size_in_bytes > MAX_FILE_SIZE:
        size = file.size_in_bytes // MAX_FILE_SIZE
        logger.warning(f"File '{file.name}' size is bigger than 50 Mb ({size}). Ignoring it")

    logger.info("Sending file...")
    input_file = InputFile(file.content, file_name=file.name)
    bot = Bot(token=settings.BALE_TOKEN)
    async with bot as b:
        await b.send_document(settings.BALE_TARGET_CHAT_ID, input_file)
    logger.info("File sent successfully")


def _get_message_chunks(message: str) -> list[str]:
    chunks: list[str] = []

    while True:
        chunk = message[:CHUNK_SIZE]
        chunks.append(chunk)
        if len(message) <= CHUNK_SIZE:
            break

        message = message[CHUNK_SIZE:]

    return chunks

