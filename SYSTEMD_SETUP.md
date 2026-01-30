# Setting Up the Bot as a Linux Systemd Service

This guide explains how to run the Telegram-to-Bale bot as a systemd service on Linux.

## Prerequisites

- Linux system with systemd (Ubuntu, Debian, CentOS, etc.)
- Python 3.14 or higher installed
- Bot dependencies installed
- Bot tested and working when run manually

## Installation Steps

### 1. Prepare the Bot Directory

Deploy your bot to a permanent location on your Linux server:

```bash
# Example: deploy to /opt/apps/bale_bot
sudo mkdir -p /opt/apps/bale_bot
sudo cp -r /path/to/your/bale_bot/* /opt/apps/bale_bot/

# Or clone from git
cd /opt
sudo git clone <your-repo-url> bale_bot
```

### 2. Install Python Dependencies

```bash
cd /opt/bale_bot

# Option A: Using system Python
sudo pip3 install -r requirements.txt

# Option B: Using virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create or copy your `.env` file with all required credentials:

```bash
sudo cp .env /opt/bale_bot/.env
# Or create it manually
sudo nano /opt/bale_bot/.env
```

Ensure your `.env` file contains:
```
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=your_phone_number
BALE_TOKEN=your_bale_token
BALE_TARGET_CHAT_ID=your_chat_id
FERNET_KEY=your_fernet_key
CHANNELS=["channel1", "channel2"]
TARGET_TELEGRAM_CHANNEL=your_target_channel
```

### 4. Create Sessions Directory

```bash
sudo mkdir -p /opt/bale_bot/sessions
```

### 5. First-Time Authentication

Before setting up the service, run the bot manually once to authenticate with Telegram:

```bash
cd /opt/bale_bot

# If using virtual environment
source venv/bin/activate

python src/main.py
```

Enter the verification code when prompted. This creates the session file in `sessions/anon.session`.

### 6. Set Ownership and Permissions

Replace `your-username` with the user that will run the service:

```bash
# Create a dedicated user (optional but recommended)
sudo useradd -r -s /bin/false telegram-bale-bot

# Set ownership
sudo chown -R telegram-bale-bot:telegram-bale-bot /opt/bale_bot

# Or use your existing user
sudo chown -R your-username:your-username /opt/bale_bot

# Set permissions
sudo chmod 600 /opt/bale_bot/.env
sudo chmod 755 /opt/bale_bot/sessions
```

### 7. Edit the Service File

Edit `telegram-bale-bot.service` and update the following placeholders:

```bash
nano telegram-bale-bot.service
```

Update these lines:
- `User=your-username` → your actual Linux username or `telegram-bale-bot`
- `Group=your-username` → your actual Linux group or `telegram-bale-bot`
- `WorkingDirectory=/path/to/bale_bot` → `/opt/bale_bot`
- `EnvironmentFile=/path/to/bale_bot/.env` → `/opt/bale_bot/.env`
- `ExecStart=...` → full path to Python and main.py

For virtual environment:
```ini
ExecStart=/opt/bale_bot/venv/bin/python /opt/bale_bot/src/main.py
```

For system Python:
```ini
ExecStart=/usr/bin/python3 /opt/bale_bot/src/main.py
```

Update `ReadWritePaths` to match your installation:
```ini
ReadWritePaths=/opt/bale_bot/sessions
```

### 8. Install the Service

```bash
# Copy service file to systemd directory
sudo cp telegram-bale-bot.service /etc/systemd/system/

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable telegram-bale-bot

# Start the service
sudo systemctl start telegram-bale-bot
```

## Managing the Service

### Check Service Status

```bash
sudo systemctl status telegram-bale-bot
```

### View Logs

```bash
# View recent logs
sudo journalctl -u telegram-bale-bot -n 100

# Follow logs in real-time
sudo journalctl -u telegram-bale-bot -f

# View logs since last boot
sudo journalctl -u telegram-bale-bot -b
```

### Start/Stop/Restart

```bash
# Start
sudo systemctl start telegram-bale-bot

# Stop
sudo systemctl stop telegram-bale-bot

# Restart
sudo systemctl restart telegram-bale-bot

# Reload configuration
sudo systemctl daemon-reload
sudo systemctl restart telegram-bale-bot
```

### Enable/Disable Auto-Start

```bash
# Enable auto-start on boot
sudo systemctl enable telegram-bale-bot

# Disable auto-start
sudo systemctl disable telegram-bale-bot
```

## Troubleshooting

### Service won't start

```bash
# Check service status for errors
sudo systemctl status telegram-bale-bot

# Check detailed logs
sudo journalctl -u telegram-bale-bot -n 50 --no-pager
```

### Permission errors

```bash
# Verify ownership
ls -la /opt/bale_bot

# Fix permissions
sudo chown -R telegram-bale-bot:telegram-bale-bot /opt/bale_bot
```

### Environment variables not loaded

```bash
# Verify .env file exists and has correct permissions
ls -la /opt/bale_bot/.env

# Test loading environment manually
sudo -u telegram-bale-bot bash -c 'cd /opt/bale_bot && python3 src/main.py'
```

### Session file issues

If you get authentication errors:
1. Stop the service: `sudo systemctl stop telegram-bale-bot`
2. Remove session file: `sudo rm /opt/bale_bot/sessions/anon.session`
3. Run manually to re-authenticate: `sudo -u telegram-bale-bot python3 /opt/bale_bot/src/main.py`
4. Start service: `sudo systemctl start telegram-bale-bot`

## Security Recommendations

1. **Use a dedicated user**: Create a specific user for the bot with limited permissions
2. **Protect credentials**: Ensure `.env` has restricted permissions (600)
3. **Limit write access**: Only the sessions directory needs write access
4. **Regular updates**: Keep dependencies updated for security patches
5. **Monitor logs**: Regularly check logs for unusual activity

## Updating the Bot

When updating the code:

```bash
# Stop the service
sudo systemctl stop telegram-bale-bot

# Update code
cd /opt/bale_bot
sudo -u telegram-bale-bot git pull  # if using git
# Or manually copy updated files

# Update dependencies if needed
sudo -u telegram-bale-bot /opt/bale_bot/venv/bin/pip install -r requirements.txt

# Start the service
sudo systemctl start telegram-bale-bot

# Verify it's running
sudo systemctl status telegram-bale-bot
```
