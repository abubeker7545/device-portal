# Telegram Bot for Classified Ads Mini App

This Telegram bot integrates with your Next.js classified ads frontend, allowing users to access the full application as a Telegram Mini App.

## Features

- 🚀 **Mini App Integration**: Opens the Next.js frontend as a Telegram Mini App
- 🔍 **Smart Search**: Helps users find listings through natural language
- 📱 **Mobile Optimized**: Perfect for mobile users browsing classified ads
- 🔔 **Notifications**: Can send updates about new listings and messages
- 🛡️ **Secure**: Webhook-based with secret token verification

## Setup

### 1. Create a Telegram Bot

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Use `/newbot` command to create a new bot
3. Follow the instructions to get your bot token
4. Use `/setmenubutton` to set up the mini app button (optional)

### 2. Configure Environment Variables

Copy `env.example` to `.env` and fill in your values:

```bash
cp env.example .env
```

Edit `.env`:
```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_WEBHOOK_URL=https://yourdomain.com
TELEGRAM_WEBHOOK_SECRET=your_webhook_secret_here

# Next.js Frontend Configuration
FRONTEND_URL=https://yourdomain.com
FRONTEND_PORT=3000

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Bot

#### Option A: Polling Mode (Development)
```bash
python bot.py
```

#### Option B: Webhook Mode (Production)
```bash
python webhook_server.py
```

## Configuration

### Frontend URL
Make sure your Next.js frontend is accessible at the URL specified in `FRONTEND_URL`. The bot will open this URL as a mini app.

### Webhook Setup (Production)
For production deployment, you'll need to:

1. Deploy the webhook server to a public URL
2. Set the `TELEGRAM_WEBHOOK_URL` to your deployed server
3. Configure your webhook secret for security
4. Set up SSL certificate (required by Telegram)

### Mini App Configuration
To set up the mini app button in your bot:

1. Use `/setmenubutton` command with BotFather
2. Set the button text (e.g., "Open App")
3. Set the web app URL to your frontend URL

## Bot Commands

- `/start` - Welcome message and main menu
- `/help` - Show help information
- `/app` - Open the mini app directly

## Integration with Next.js

The bot opens your Next.js frontend as a mini app. Make sure your frontend:

1. Is responsive and mobile-friendly
2. Handles Telegram Mini App initialization
3. Can receive data from Telegram (user info, etc.)

### Telegram Mini App Integration

Add this to your Next.js app to handle Telegram Mini App:

```javascript
// In your Next.js app
useEffect(() => {
  if (window.Telegram?.WebApp) {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();
    
    // Get user data
    const user = tg.initDataUnsafe?.user;
    console.log('Telegram user:', user);
  }
}, []);
```

## Development

### Local Development
1. Run your Next.js frontend: `npm run dev` (in frontend directory)
2. Set `FRONTEND_URL=http://localhost:3000` in `.env`
3. Run the bot in polling mode: `python bot.py`

### Testing
- Test the bot by messaging it on Telegram
- Use the "Open App" button to test mini app functionality
- Check logs for any errors

## Deployment

### Using Docker (Recommended)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "webhook_server.py"]
```

### Using PM2
```bash
pm2 start webhook_server.py --name telegram-bot
```

## Security

- Always use HTTPS in production
- Set a strong webhook secret
- Validate incoming webhook requests
- Keep your bot token secure

## Troubleshooting

### Common Issues

1. **Bot not responding**: Check if the bot token is correct
2. **Mini app not opening**: Verify the frontend URL is accessible
3. **Webhook errors**: Check if the webhook URL is publicly accessible and uses HTTPS

### Logs
Check the console output for detailed error messages and debugging information.

## Support

For issues and questions:
1. Check the logs for error messages
2. Verify your configuration
3. Test with a simple message first
4. Check Telegram's bot documentation