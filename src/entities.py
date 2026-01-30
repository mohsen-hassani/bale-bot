import logging

from dataclasses import dataclass

from telethon import TelegramClient
from telethon.tl.types import (
    Document,
    Photo,
    MessageEntityTextUrl,
    Message as TelegramMessage,
)

logger = logging.getLogger(__name__)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes


@dataclass
class Button:
    label: str
    link: str


@dataclass
class File:
    name: str
    size_in_bytes: int
    content: bytes
    id: int
    mime_type: str


class MessageBuilder:
    def __init__(self):
        self.telegram_message: TelegramMessage | None = None
        self.telegram_client: TelegramClient | None = None

    async def build_message_from_telegram_event(self, event) -> Message:
        self.telegram_message = event.message
        self.telegram_client = event.client
        payload: str = event.message.raw_text

        buttons: list[Button] = []
        file: File | None = None
        photo: File | None = None
        entities: set[str] = set()

        if event.message.document and isinstance(event.message.document, Document):
            photo: File | None = await self._get_photo(event.message.media.photo)

        if event.message.media and isinstance(event.message.media.photo, Photo):
            photo: File | None = await self._get_photo(event.message.media.photo)

        if event.message.buttons:
            buttons = await self._get_buttons()

        if event.message.entities:
            for entity in event.message.entities:
                if isinstance(entity, MessageEntityTextUrl):
                    entities.add(entity.url)

        return Message(
            source_channel_id=event.message.chat.id,
            source_channel_username=event.message.chat.username,
            body=payload,
            links=list(entities),
            buttons=buttons,
            file=file,
            photo=photo,
        )

    async def _get_photo(self, photo: Photo) -> File | None:
        # Get the largest photo size
        largest_size = photo.sizes[-1]
        photo_size = largest_size.size if hasattr(largest_size, 'size') else 0

        if photo_size > MAX_FILE_SIZE:
            logger.warning(f"Skipping photo: size {photo_size} bytes exceeds 50MB limit")
            return None

        try:
            logger.info(f"Downloading photo ({photo_size} bytes)...")
            photo_content: bytes = await self.telegram_client.download_media(
                self.telegram_message,
                file=bytes,  # noqa
            )
            photo = File(
                id=photo.id,
                size_in_bytes=len(photo_content),
                mime_type="image/jpeg",
                name="photo.jpg",
                content=photo_content,
            )
            logger.info("Photo downloaded successfully")
            return photo
        except Exception as e:
            logger.error(f"Failed to download photo: {e}")
            return None

    async def _get_file(self, doc: Document) -> File | None:
        if doc.size > MAX_FILE_SIZE:
            logger.warning(f"Skipping file: size {doc.size} bytes exceeds 50MB limit")
            return None

        try:
            file_name = doc.attributes[0].file_name if doc.attributes else "unknown_file"
            logger.info(f"Downloading file '{file_name}' ({doc.size} bytes)...")
            file_content: bytes = await self.telegram_client.download_media(
                self.telegram_message,
                file=bytes,  # noqa
            )
            file = File(
                id=doc.id,
                size_in_bytes=doc.size,
                mime_type=doc.mime_type,
                name=file_name,
                content=file_content,
            )
            logger.info("File downloaded successfully")
            return file
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            return None

    async def _get_buttons(self) -> list[Button]:
        if self.telegram_message is None:
            return []
        message: TelegramMessage = self.telegram_message

        buttons = []
        unique_urls: set[str] = set()
        for button_set in message.buttons:
            for button in button_set:
                if button.url in unique_urls:
                    continue

                unique_urls.add(button.url)
                buttons.append(Button(label=button.text, link=button.url))

        return buttons



@dataclass
class Message:
    source_channel_id: str
    source_channel_username: str
    body: str
    links: list[str]
    buttons: list[Button]
    file: File | None = None
    photo: File | None = None

