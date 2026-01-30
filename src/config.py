import json
import logging
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()
    ]
)


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        extra='ignore'
    )

    TELEGRAM_API_ID: int
    TELEGRAM_API_HASH: str
    TELEGRAM_PHONE: str
    BALE_TOKEN: str
    BALE_TARGET_CHAT_ID: int
    FERNET_KEY: str
    CHANNELS: str

    @field_validator('FERNET_KEY', mode='before')
    @classmethod
    def encode_fernet_key(cls, v):
        """Keep FERNET_KEY as string, will be encoded when needed"""
        return v

    @field_validator('CHANNELS', mode='before')
    @classmethod
    def parse_channels(cls, v):
        """Parse CHANNELS from JSON string if needed"""
        if isinstance(v, str):
            return v
        return json.dumps(v)

    def get_fernet_key_bytes(self) -> bytes:
        """Get FERNET_KEY as bytes"""
        return self.FERNET_KEY.encode()

    def get_channels_list(self) -> list[str]:
        """Get CHANNELS as a list"""
        return json.loads(self.CHANNELS)


settings = BotSettings()  # noqa
