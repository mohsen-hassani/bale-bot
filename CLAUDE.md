# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Telegram-to-Bale message forwarding bot that monitors specified Telegram channels and forwards encrypted messages to a Bale chat. The bot uses Telethon for Telegram integration and the Bale Bot API for message delivery.

## Key Dependencies

- **Telethon** (`1.40.0`): Telegram client library for monitoring channels
- **python-bale-bot** (`2.5.0`): Bale messaging platform integration
- **cryptography**: Fernet encryption for message payloads
- **lzma**: Message compression before encryption
- **requests**: HTTP client for Bale API calls

## Project Structure

```
bale_bot/
├── src/
│   ├── main.py           # Primary bot implementation (Telegram → Bale forwarding)
│   ├── basic.py          # Simple Bale bot example
│   ├── telethon_test.py  # Telethon testing/experimentation
│   └── utils.py          # Utility functions for Bale API
├── main.py               # Entry point placeholder
├── pyproject.toml        # UV project configuration
└── requirements.txt      # Python dependencies
```

## Development Commands

### Environment Setup

```bash
# Install dependencies using uv
uv sync

# Or install dependencies using pip
pip install -r requirements.txt
```

### Running the Bot

The main bot implementation is in `src/main.py`:

```bash
# Run the Telegram-to-Bale forwarding bot
python src/main.py
```

Other available scripts:
```bash
# Run the basic Bale bot example
python src/basic.py

# Run Telethon testing script
python src/telethon_test.py
```

## Architecture

### Message Flow (src/main.py)

1. **Telegram Listener**: Monitors specified channels using Telethon event handlers
   - Listens to multiple channels defined in `CHANNELS` list
   - Captures message text, buttons, and embedded URLs

2. **Message Processing**:
   - Extracts message payload, username, channel ID, buttons, and entities
   - Serializes data to JSON format
   - Compresses using LZMA
   - Encrypts using Fernet symmetric encryption

3. **Bale Delivery**:
   - Sends encrypted payload to Bale via HTTP API
   - Automatically chunks messages over 3000 characters
   - Posts to configured Bale chat ID

### Configuration

All configuration is hardcoded in `src/main.py`:
- `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`: Telegram API credentials
- `BALE_TOKEN`, `BALE_TARGET_CHAT_ID`: Bale bot configuration
- `FERNET_KEY`: Encryption key for message payload
- `CHANNELS`: List of Telegram channels to monitor

**Security Note**: Credentials are currently hardcoded. For production, these should be moved to environment variables or a secure configuration file.

### Key Functions

- `send_message_to_bale(message: str)`: Sends message to Bale, handling chunking for long messages
- `encrypt_message(raw_message)`: Compresses and encrypts message payload
- `handler(event)`: Async event handler for new Telegram messages

## Important Notes

- The bot uses a session file (`anon.session`) created by Telethon for persistent authentication
- Messages are encrypted before forwarding to ensure privacy
- The bot requires phone verification on first run for Telegram authentication
- All logging is configured at INFO level with StreamHandler output
