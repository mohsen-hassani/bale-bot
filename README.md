# Telegram Message Forwarding Bot

A robust message forwarding bot that monitors Telegram channels and forwards messages to either Bale (with encryption) or another Telegram channel. Built with Telethon and featuring a publisher-subscriber architecture for extensibility.

## Features

### Core Functionality
- **Multi-Channel Monitoring**: Monitor multiple Telegram channels simultaneously
- **Dual Forwarding Modes**:
  - **Telegram → Bale**: Encrypted message forwarding with compression
  - **Telegram → Telegram**: Direct message forwarding between channels
- **Rich Media Support**: Forward photos and files up to 50MB
- **Button & Link Extraction**: Preserve inline buttons and embedded URLs
- **Message Chunking**: Automatically splits long messages for delivery

### Security & Reliability
- **End-to-End Encryption**: Fernet symmetric encryption for Bale messages
- **LZMA Compression**: Reduces payload size before encryption
- **Session Persistence**: Telegram authentication stored locally
- **Auto-Restart**: Systemd service configuration included
- **Docker Support**: Containerized deployment ready

### Architecture
- **Publisher-Subscriber Pattern**: Extensible event-driven architecture
- **Type-Safe Configuration**: Pydantic-based settings management
- **Structured Logging**: Comprehensive logging with Python's logging module
- **Async/Await**: Non-blocking I/O for optimal performance

## Table of Contents
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Running Locally](#running-locally)
  - [Running with Docker](#running-with-docker)
  - [Running as Linux Service](#running-as-linux-service)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites
- Python 3.11 or higher
- Telegram API credentials ([obtain here](https://my.telegram.org/apps))
- Bale bot token (if using Bale forwarding mode)

### Local Installation

```bash
# Clone the repository
git clone <repository-url>
cd bale_bot

# Install dependencies
pip install -r requirements.txt

# Or use UV (recommended)
uv sync
```

### Docker Installation

```bash
# Build the Docker image
docker compose build

# Or pull from registry (if available)
docker pull <image-name>
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Telegram Configuration
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+1234567890

# Bale Configuration (for Bale forwarding mode)
BALE_TOKEN=your_bale_bot_token
BALE_TARGET_CHAT_ID=123456789
FERNET_KEY=your_base64_encoded_fernet_key

# Channel Configuration
CHANNELS=["channel_username1", "channel_username2"]
TARGET_TELEGRAM_CHANNEL=destination_channel_username
```

### Configuration Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `TELEGRAM_API_ID` | Yes | Telegram API ID from my.telegram.org |
| `TELEGRAM_API_HASH` | Yes | Telegram API hash from my.telegram.org |
| `TELEGRAM_PHONE` | Yes | Phone number for Telegram authentication |
| `BALE_TOKEN` | Bale mode | Bale bot authentication token |
| `BALE_TARGET_CHAT_ID` | Bale mode | Destination Bale chat ID |
| `FERNET_KEY` | Bale mode | Encryption key (generate with `cryptography.fernet.Fernet.generate_key()`) |
| `CHANNELS` | Yes | JSON array of source Telegram channels |
| `TARGET_TELEGRAM_CHANNEL` | Telegram mode | Destination Telegram channel username |

### Generating a Fernet Key

```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # Use this in your .env file
```

## Usage

### Running Locally

#### Telegram → Bale Mode (with encryption)

```bash
python src/main.py
```

On first run, you'll be prompted to enter a verification code sent to your Telegram account.

#### Telegram → Telegram Mode (direct forwarding)

```bash
python src/telegram_listener.py
```

### Running with Docker

#### Build and Run

```bash
# Run in foreground (for first-time authentication)
docker compose up --build

# Run in background (after authentication)
docker compose up -d
```

#### Attach to Running Container

```bash
# Attach to see logs and interact
docker attach telegram-bale-bot

# Detach without stopping: Ctrl+P, Ctrl+Q
```

#### View Logs

```bash
# Follow logs
docker compose logs -f bale-bot

# View last 100 lines
docker compose logs --tail=100 bale-bot
```

#### Stop Container

```bash
docker compose down
```

### Running as Linux Service

For production deployments, run the bot as a systemd service:

```bash
# Edit service file with your paths
nano telegram-bale-bot.service

# Install service
sudo cp telegram-bale-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable telegram-bale-bot
sudo systemctl start telegram-bale-bot

# Check status
sudo systemctl status telegram-bale-bot

# View logs
sudo journalctl -u telegram-bale-bot -f
```

See [SYSTEMD_SETUP.md](SYSTEMD_SETUP.md) for detailed installation instructions.

## Architecture

### Project Structure

```
bale_bot/
├── src/
│   ├── main.py                 # Telegram→Bale forwarding entry point
│   ├── telegram_listener.py    # Telegram→Telegram forwarding entry point
│   ├── config.py               # Pydantic settings configuration
│   ├── entities.py             # Message, Button, File dataclasses
│   └── pubsub/
│       ├── base.py             # Publisher/Subscriber pattern
│       └── subscribers.py      # BaleSubscriber implementation
├── sessions/                   # Telegram session files (auto-created)
├── Dockerfile                  # Docker image configuration
├── docker-compose.yml          # Docker compose configuration
├── telegram-bale-bot.service   # Systemd service file
├── requirements.txt            # Python dependencies
└── .env                        # Environment configuration
```

### Message Flow (Telegram → Bale)

```
Telegram Event
     ↓
MessageBuilder (entities.py)
     ↓
Message Object (with buttons, files, links)
     ↓
Publisher.publish() (pubsub/base.py)
     ↓
BaleSubscriber.__call__() (pubsub/subscribers.py)
     ↓
Encryption (Fernet) + Compression (LZMA)
     ↓
Chunking (if > 2000 chars)
     ↓
Bale API (aiohttp)
```

### Publisher-Subscriber Pattern

The bot uses a flexible pub/sub architecture:

- **Publisher**: Manages channels and broadcasts messages
- **Channel**: Contains subscribers for a specific topic
- **Subscriber**: Callable that processes published messages
- **BaleSubscriber**: Encrypts and forwards to Bale

This pattern allows easy extension to support additional platforms (Discord, Slack, etc.) by implementing new subscribers.

## API Reference

### Core Classes

#### `MessageBuilder`
Builds structured `Message` objects from Telegram events.

```python
builder = MessageBuilder()
message = await builder.build_message_from_telegram_event(event)
```

#### `Message` (Dataclass)
```python
@dataclass
class Message:
    source_channel_id: str
    source_channel_username: str
    body: str
    links: list[str]
    buttons: list[Button]
    file: File | None
    photo: File | None
```

#### `BaleSubscriber`
Encrypts and forwards messages to Bale.

```python
subscriber = BaleSubscriber()
await subscriber(message)  # Process and send message
```

#### `Publisher`
Manages message distribution.

```python
publisher = Publisher()
publisher.subscribe("channel_name", subscriber)
await publisher.publish("channel_name", message)
```

### Configuration

#### `BotSettings` (Pydantic)
```python
from config import settings

settings.TELEGRAM_API_ID        # int
settings.TELEGRAM_API_HASH      # str
settings.get_channels_list()    # list[str]
settings.get_fernet_key_bytes() # bytes
```

## Troubleshooting

### Common Issues

#### Authentication Failed
```bash
# Remove session file and re-authenticate
rm sessions/anon.session
python src/main.py
```

#### Docker Build Fails (cffi compilation)
Ensure `libffi-dev` is in the Dockerfile:
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*
```

#### Messages Not Forwarding
1. Check channel usernames are correct
2. Ensure bot has access to source channels
3. Verify environment variables are loaded:
```python
from config import settings
print(settings.get_channels_list())
```

#### Permission Denied (systemd)
```bash
# Fix ownership
sudo chown -R your-user:your-user /path/to/bale_bot

# Fix session directory
sudo chmod 755 sessions/
```

### Debug Logging

Enable debug logging by modifying `src/config.py`:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    handlers=[logging.StreamHandler()]
)
```

## Development

### Adding a New Subscriber

To forward messages to a new platform:

1. Create a new subscriber in `src/pubsub/subscribers.py`:
```python
class DiscordSubscriber:
    async def __call__(self, message: Message):
        # Process and send to Discord
        pass
```

2. Register in `src/main.py`:
```python
discord_subscriber = DiscordSubscriber()
publisher.subscribe(DEFAULT, discord_subscriber)
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

## Security Considerations

1. **Protect `.env` file**: Never commit credentials to version control
2. **Encryption keys**: Store `FERNET_KEY` securely (use secrets management in production)
3. **File size limits**: Bot enforces 50MB limit to prevent memory issues
4. **Session files**: Protect `sessions/` directory with proper permissions (chmod 700)
5. **API rate limits**: Telethon handles rate limiting automatically

## License

[Your License Here]

## Contributing

Contributions welcome! Please submit issues and pull requests.

## Support

For questions or issues:
- Open an issue on GitHub
- Check [SYSTEMD_SETUP.md](SYSTEMD_SETUP.md) for deployment help
- Review [CLAUDE.md](CLAUDE.md) for development guidelines
