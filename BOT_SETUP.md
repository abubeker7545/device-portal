# Telegram Bot Setup Guide

## Overview

The Telegram bot runs **separately** from the Flask web portal. Both services share the same database (`devices.db`) but run independently.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

Create a `.env` file in the project root:

```env
# Telegram Bot Token (required)
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Web App URL (optional, defaults to http://localhost:8080)
WEB_APP_URL=http://localhost:8080

# Optional: Webhook configuration (for production)
TELEGRAM_WEBHOOK_URL=https://yourdomain.com
TELEGRAM_WEBHOOK_SECRET=your_secret_token
```

### 3. Get Telegram Bot Token

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Use `/newbot` command
3. Follow instructions to create your bot
4. Copy the token and add it to `.env`

### 4. Run the Services

#### Terminal 1: Start Flask Web Portal
```bash
python app.py
```

The web portal will be available at:
- Main Portal: http://localhost:8080
- Admin Login: http://localhost:8080/login
- API Endpoint: http://localhost:8080/api/devices

#### Terminal 2: Start Telegram Bot
```bash
# Option 1: Using run.py (recommended)
python telegram_bot/run.py

# Option 2: Using bot.py directly
python telegram_bot/bot.py
```

The bot will start in polling mode and connect to the same database.

## Bot Commands

- `/start` - Welcome message with quick actions
- `/register` - Register a new device
- `/devices` - View all registered devices (last 20)
- `/stats` - View device statistics
- `/app` - Open the web portal
- `/help` - Show all available commands

## Architecture

```
┌─────────────────┐         ┌─────────────────┐
│   Flask App     │         │  Telegram Bot   │
│   (Port 8080)   │         │   (Polling)     │
└────────┬────────┘         └────────┬────────┘
         │                           │
         └───────────┬───────────────┘
                     │
              ┌──────▼──────┐
              │ devices.db  │
              │ (Shared DB) │
              └─────────────┘
```

## Features

✅ Bot and web portal run independently
✅ Shared database for device registration
✅ Users can register devices via Telegram or Web
✅ View devices and statistics from both interfaces
✅ Web portal accessible directly from Telegram (Mini App)

## Troubleshooting

### Bot can't find database
- Make sure `devices.db` exists in the project root
- The bot automatically looks for the database in the parent directory

### Bot not responding
- Check that `TELEGRAM_BOT_TOKEN` is set correctly in `.env`
- Verify the bot token is valid with BotFather
- Check bot logs for errors

### Database locked errors
- SQLite can handle concurrent reads
- For heavy usage, consider using a more robust database

## Production Deployment

For production:
1. Use webhook mode instead of polling
2. Set up HTTPS (required for webhooks)
3. Configure `TELEGRAM_WEBHOOK_URL` and `TELEGRAM_WEBHOOK_SECRET`
4. Use a proper database (PostgreSQL, MySQL) instead of SQLite

