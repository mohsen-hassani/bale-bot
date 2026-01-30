# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Telegram message forwarding bot with two operational modes:

1. **Telegram → Bale Mode** (`src/main.py`): Monitors Telegram channels, encrypts messages with Fernet, compresses with LZMA, and forwards to Bale messaging platform using a publisher-subscriber architecture.

2. **Telegram → Telegram Mode** (`src/telegram_listener.py`): Directly forwards messages from monitored Telegram channels to a target Telegram channel.

The bot is built with an extensible publisher-subscriber pattern, making it easy to add new forwarding destinations.

## Key Technologies

- **Telethon** (`1.40.0`): Telegram client library for monitoring channels and message events
- **python-bale-bot** (`2.5.0`): Bale messaging platform SDK for message delivery
- **cryptography** (`45.0.4`): Fernet symmetric encryption for message payloads
- **pydantic** (`2.12.5`) / **pydantic-settings** (`2.12.0`): Type-safe configuration management
- **aiohttp** (`3.9.1`): Async HTTP client for Bale API calls
- **lzma**: Built-in Python module for message compression
- **asyncio**: Core async/await event loop

## Project Structure

```
bale_bot/
├── src/
│   ├── main.py                 # Telegram→Bale forwarding entry point
│   ├── telegram_listener.py    # Telegram→Telegram forwarding entry point
│   ├── config.py               # Pydantic-based settings with .env support
│   ├── entities.py             # Domain models (Message, Button, File, MessageBuilder)
│   └── pubsub/
│       ├── __init__.py
│       ├── base.py             # Publisher, Channel, Subscriber protocol
│       └── subscribers.py      # BaleSubscriber implementation
├── sessions/                   # Telegram session files (auto-created)
├── Dockerfile                  # Multi-stage Docker build
├── docker-compose.yml          # Docker Compose configuration
├── telegram-bale-bot.service   # Systemd service file
├── SYSTEMD_SETUP.md           # Service installation guide
├── requirements.txt            # Pinned Python dependencies
├── pyproject.toml             # UV project configuration
├── .env                       # Environment variables (not in git)
└── .env.example               # Example environment configuration
```

## Architecture

### Publisher-Subscriber Pattern

The bot uses a flexible event-driven architecture:

**Core Components:**
- `Publisher`: Central message broker managing multiple channels
- `Channel`: Topic-specific message distribution to subscribers
- `Subscriber[T]`: Protocol defining async callable interface `async def __call__(self, message: Message)`
- `BaleSubscriber`: Concrete subscriber that encrypts and forwards to Bale

**Message Flow:**
```
Telegram Event (events.NewMessage)
    ↓
MessageBuilder.build_message_from_telegram_event()
    ↓
Message (dataclass with body, buttons, links, files, photos)
    ↓
Publisher.publish(channel_name, message)
    ↓
Channel.publish(message) → iterates subscribers
    ↓
BaleSubscriber.__call__(message)
    ↓
1. Serialize to JSON
2. Compress with lzma.compress()
3. Encrypt with Fernet
4. Chunk if > 2000 chars
5. Send via aiohttp to Bale API
6. Send files/photos separately
```

### Domain Models (entities.py)

**`Message` (dataclass):**
- `source_channel_id`: Telegram chat ID
- `source_channel_username`: Channel username
- `body`: Message text content
- `links`: Extracted URLs from entities
- `buttons`: List of `Button` objects from inline keyboard
- `file`: Optional `File` object (up to 50MB)
- `photo`: Optional `File` object for images

**`MessageBuilder`:**
- Async factory for creating `Message` objects from Telethon events
- Downloads photos/files (respecting 50MB limit)
- Extracts inline buttons and URL entities
- Handles Telegram media types (Document, Photo)

**`File` (dataclass):**
- `name`, `size_in_bytes`, `content` (bytes), `id`, `mime_type`

**`Button` (dataclass):**
- `label`, `link`

### Configuration System (config.py)

Uses Pydantic `BaseSettings` for type-safe configuration:

```python
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
    CHANNELS: str  # JSON array as string
    TARGET_TELEGRAM_CHANNEL: str

    def get_channels_list(self) -> list[str]:
        return json.loads(self.CHANNELS)

    def get_fernet_key_bytes(self) -> bytes:
        return self.FERNET_KEY.encode()
```

Singleton instance: `settings = BotSettings()`

### Logging

Configured in `config.py`:
```python
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)
```

All modules use: `logger = logging.getLogger(__name__)`

## Development Commands

### Environment Setup

```bash
# Using UV (recommended)
uv sync

# Using pip
pip install -r requirements.txt

# Create .env file
cp .env.example .env  # then edit with credentials
```

### Running the Bot

**Telegram → Bale Mode:**
```bash
python src/main.py
```

**Telegram → Telegram Mode:**
```bash
python src/telegram_listener.py
```

**First-time authentication:** On first run, Telethon will prompt for a verification code sent to the configured phone number.

### Docker

```bash
# Build and run (interactive for first auth)
docker compose up --build

# Run in background
docker compose up -d

# View logs
docker compose logs -f bale-bot

# Attach to container
docker attach telegram-bale-bot

# Detach without stopping: Ctrl+P, Ctrl+Q
```

### Systemd Service

See [SYSTEMD_SETUP.md](SYSTEMD_SETUP.md) for complete installation guide.

```bash
# Quick start
sudo cp telegram-bale-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable telegram-bale-bot
sudo systemctl start telegram-bale-bot

# View logs
sudo journalctl -u telegram-bale-bot -f
```

## Configuration Requirements

### Required Environment Variables

All configuration is loaded from `.env` file:

```env
# Telegram API credentials (from https://my.telegram.org/apps)
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
TELEGRAM_PHONE=+1234567890

# Bale configuration (for Bale mode)
BALE_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
BALE_TARGET_CHAT_ID=123456789

# Encryption key (generate with: Fernet.generate_key().decode())
FERNET_KEY=base64_encoded_key_here

# Channels to monitor (JSON array)
CHANNELS=["channel_username1", "channel_username2", "@channel3"]

# Target channel for Telegram→Telegram mode
TARGET_TELEGRAM_CHANNEL=destination_channel_username
```

### Generating Encryption Key

```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # Use this value in .env
```

## Key Functions and Classes

### main.py Entry Point

```python
async def main():
    # 1. Setup pub/sub
    channel = Channel()
    bale_subscriber = BaleSubscriber()
    publisher.channels[DEFAULT] = channel
    publisher.subscribe(DEFAULT, bale_subscriber)

    # 2. Create Telegram client
    client = TelegramClient("anon", settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
    await client.start(phone=settings.TELEGRAM_PHONE)

    # 3. Register event handler
    client.add_event_handler(handler, events.NewMessage(chats=settings.get_channels_list()))

    # 4. Run until disconnected
    await client.run_until_disconnected()

async def handler(event):
    builder = MessageBuilder()
    message = await builder.build_message_from_telegram_event(event)
    await publisher.publish(DEFAULT, message)
```

### BaleSubscriber (subscribers.py)

Key methods:
- `__call__(message)`: Main entry point, orchestrates serialization → encryption → sending
- `encrypt_message(raw_message)`: LZMA compress → Fernet encrypt → base64 decode to string

Helper functions:
- `send_message_to_bale(message)`: Chunks message and sends via aiohttp
- `send_file_to_bale(file)`: Sends File object using Bale SDK's InputFile
- `_get_message_chunks(message)`: Splits into 2000-char chunks

### MessageBuilder (entities.py)

Key methods:
- `build_message_from_telegram_event(event)`: Main factory method
- `_get_photo(photo)`: Downloads photo if < 50MB
- `_get_file(doc)`: Downloads document if < 50MB
- `_get_buttons()`: Extracts unique inline keyboard buttons

## Important Implementation Details

### Session Management

- **Session files**: Stored in `sessions/` directory (for Docker) or current directory (`anon.session`)
- **First run**: Requires interactive phone verification
- **Persistence**: Session files allow bot to reconnect without re-authentication
- **Docker volume**: `./sessions:/app/sessions` for persistence across container restarts

### File Size Limits

**50MB maximum** enforced in multiple places:
- `MAX_FILE_SIZE = 50 * 1024 * 1024` in `entities.py`
- Checked in `_get_photo()` and `_get_file()`
- Re-checked in `send_file_to_bale()`

Rationale: Memory constraints and Bale API limits.

### Message Chunking

- Bale messages limited to ~4096 chars, bot uses conservative 2000 char chunks
- `CHUNK_SIZE = 2000` in `subscribers.py`
- Each chunk labeled: `"======== PART {index + 1} OF {len(chunks)} ========"`

### Error Handling

- `telegram_listener.py`: Handles `FloodWaitError` and `RPCError` explicitly
- All async functions have try/except with logging
- Systemd service configured with `Restart=always` and `RestartSec=10`

### Security

1. **Encryption**: Fernet (symmetric AES-128 CBC) with LZMA pre-compression
2. **Credentials**: Never hardcoded, always from environment
3. **Docker**: Uses `stdin_open: true` and `tty: true` for interactive auth
4. **Systemd**: Security hardening options in service file (NoNewPrivileges, PrivateTmp, etc.)

## Extending the Bot

### Adding a New Subscriber

To forward messages to another platform (Discord, Slack, etc.):

1. **Create subscriber class** in `src/pubsub/subscribers.py`:
```python
class DiscordSubscriber:
    def __init__(self):
        self.webhook_url = settings.DISCORD_WEBHOOK_URL

    async def __call__(self, message: Message):
        payload = {
            "content": message.body,
            "embeds": [{"title": b.label, "url": b.link} for b in message.buttons]
        }
        async with aiohttp.ClientSession() as session:
            await session.post(self.webhook_url, json=payload)
```

2. **Register in main.py**:
```python
discord_subscriber = DiscordSubscriber()
publisher.subscribe(DEFAULT, discord_subscriber)
```

3. **Add configuration** to `config.py`:
```python
DISCORD_WEBHOOK_URL: str
```

### Adding New Message Processing

To transform messages before publishing:

1. Modify `handler()` in `main.py` before `publisher.publish()`
2. Or create a preprocessing subscriber that publishes to a second channel
3. Or modify `MessageBuilder` to add custom fields to `Message`

## Troubleshooting Guide

### Bot Not Receiving Messages

1. **Check channel access**: Ensure phone number account has access to source channels
2. **Verify channel names**: Must be exact usernames (with or without @)
3. **Check logs**: `logger.info()` statements throughout codebase
4. **Test event handler**: Add debug logging to `handler()` function

### Authentication Issues

```bash
# Remove session and re-authenticate
rm sessions/anon.session  # or just anon.session
python src/main.py
```

### Docker Build Failures

**Common issue**: `cffi` compilation fails with "ffi.h: No such file or directory"

**Solution**: Ensure `libffi-dev` in Dockerfile:
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*
```

### Environment Variables Not Loading

1. **Check .env location**: Must be in project root (parent of `src/`)
2. **Verify config.py path**: `env_file=Path(__file__).parent.parent / ".env"`
3. **Test loading**:
```python
from src.config import settings
print(settings.model_dump())
```

### Message Encryption Errors

- **Fernet key format**: Must be valid base64-encoded 32-byte key
- **Generate new key**: `Fernet.generate_key().decode()`
- **Check encoding**: `settings.get_fernet_key_bytes()` should not raise

## Code Style and Conventions

### Type Hints

- All functions use type hints
- Dataclasses for structured data
- Protocol classes for interfaces (e.g., `Subscriber[T]`)
- Generic types with square bracket notation (Python 3.12+ syntax)

### Async/Await

- All I/O operations are async
- Use `asyncio.run()` for entry point
- Context managers for clients: `async with aiohttp.ClientSession():`

### Logging

- Use module-level logger: `logger = logging.getLogger(__name__)`
- Log levels: INFO for normal flow, WARNING for skipped operations, ERROR for exceptions
- Include context: `logger.info(f"Downloading file '{file_name}' ({doc.size} bytes)...")`

### Dataclasses

- Prefer dataclasses over dictionaries for structured data
- Use `@dataclass` decorator
- Include type hints for all fields
- Use `field(default_factory=...)` for mutable defaults

## Testing

Currently no automated tests. To test manually:

1. **Test authentication**: `python src/main.py` should prompt for code
2. **Test message forwarding**: Send test message to monitored channel
3. **Test file handling**: Send image/document to monitored channel
4. **Test chunking**: Send very long message (>2000 chars)
5. **Test buttons**: Forward message with inline keyboard

## Dependencies Management

### Critical Dependencies

- `telethon==1.40.0`: Telegram client
- `python-bale-bot==2.5.0`: Bale SDK
- `cryptography==45.0.4`: Encryption
- `pydantic-settings==2.12.0`: Configuration
- `aiohttp==3.9.1`: HTTP client

### Updating Dependencies

```bash
# Update requirements.txt
pip freeze > requirements.txt

# Or use UV
uv lock
```

**Warning**: Test thoroughly after updates, especially Telethon (API changes).

## Deployment Checklist

- [ ] Create `.env` file with all required variables
- [ ] Generate Fernet encryption key
- [ ] Run manually first time to authenticate Telegram
- [ ] Verify session file created (`sessions/anon.session` or `anon.session`)
- [ ] Test message forwarding with sample message
- [ ] Configure systemd service paths if using service mode
- [ ] Set up log rotation if running as service
- [ ] Secure `.env` file permissions (chmod 600)
- [ ] Set up monitoring/alerting for production

## Performance Considerations

- **Async I/O**: All network operations are non-blocking
- **Session reuse**: Telegram session persists across restarts
- **Chunking**: Large messages split to avoid timeouts
- **File limits**: 50MB max prevents memory exhaustion
- **Rate limiting**: Telethon handles Telegram rate limits automatically

## Security Considerations

1. **Never commit `.env`**: Add to `.gitignore`
2. **Rotate encryption keys**: Periodically regenerate `FERNET_KEY`
3. **Secure session files**: chmod 700 on `sessions/` directory
4. **Use systemd security features**: NoNewPrivileges, PrivateTmp, ProtectSystem
5. **Validate inputs**: Bot trusts Telegram API responses (consider adding validation for untrusted sources)
6. **Audit logs**: Review logs for unauthorized access patterns

## Future Enhancement Ideas

- [ ] Add webhook mode for Bale instead of polling
- [ ] Support for video forwarding
- [ ] Database logging of forwarded messages
- [ ] Admin commands via Telegram bot interface
- [ ] Multi-destination routing (conditional forwarding)
- [ ] Message transformation/filtering before forwarding
- [ ] Metrics and monitoring (Prometheus/Grafana)
- [ ] Unit tests with pytest
- [ ] CI/CD pipeline with GitHub Actions
