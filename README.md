# Device Registration Portal

A comprehensive device registration system with web portal and Telegram bot integration. Users can register devices through a web interface or Telegram bot, with secure admin dashboard for device management.

## 🚀 Features

- **Web Portal**: Beautiful, responsive web interface for device registration
- **Telegram Bot**: Register devices directly from Telegram
- **Admin Dashboard**: Secure admin panel with device management
- **REST API**: Complete API for device management and statistics
- **Mobile Responsive**: Optimized for all devices
- **Secure**: Password hashing, session management, and input validation

## 📋 Table of Contents

- [Features](#-features)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Telegram Bot Token (for bot functionality)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd tgfinal
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment

Create a `.env` file in the project root:

```bash
# Option 1: Use setup script (recommended)
python setup_env.py

# Option 2: Create manually
# Windows:
copy .env.example .env
# Linux/Mac:
cp .env.example .env
```

Edit `.env` and add your configuration (see [Configuration](#-configuration))

### Step 5: Initialize Database

The database will be automatically created on first run. You can also manually initialize:

```bash
python app.py
```

## ⚙️ Configuration

Create a `.env` file in the project root with the following variables:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development  # or 'production'
WEB_APP_URL=http://localhost:8080  # or your production URL

# Telegram Bot Configuration (Optional)
TELEGRAM_BOT_TOKEN=your_bot_token_here
FRONTEND_URL=http://localhost:8080  # or your production URL

# Database
DB_FILE=devices.db  # SQLite database file
```

### Getting a Telegram Bot Token

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Use `/newbot` command
3. Follow instructions to create your bot
4. Copy the token and add it to `.env`

## 🚀 Usage

### Running the Web Portal

```bash
python app.py
```

The web portal will be available at:
- Main Portal: http://localhost:8080
- Admin Login: http://localhost:8080/login
- Admin Dashboard: http://localhost:8080/admin

**Default Admin Credentials:**
- Username: `admin`
- Password: `1234`

⚠️ **Change the default password in production!**

### Running the Telegram Bot

In a separate terminal:

```bash
# Option 1: Using run.py (recommended)
python telegram_bot/run.py

# Option 2: Using bot.py directly
python telegram_bot/bot.py
```

### Bot Commands

- `/start` - Welcome message with quick actions
- `/register` - Register a new device
- `/devices` - View all registered devices (last 20)
- `/stats` - View device statistics
- `/app` - Open the web portal
- `/help` - Show all available commands

## 📚 API Documentation

Complete API documentation is available in [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)

### Quick API Examples

```bash
# Get all devices
curl http://localhost:8080/api/devices

# Get device by ID
curl http://localhost:8080/api/devices/1

# Check if device exists
curl "http://localhost:8080/api/devices/check?name=My%20Device"

# Search devices
curl "http://localhost:8080/api/devices/search?q=iPhone"

# Get statistics
curl http://localhost:8080/api/devices/stats
```

## 📁 Project Structure

```
tgfinal/
├── app.py                      # Flask application
├── requirements.txt            # Python dependencies
├── devices.db                  # SQLite database (auto-generated)
├── .env                        # Environment variables (create from .env.example)
├── .gitignore                  # Git ignore rules
├── README.md                   # This file
├── API_DOCUMENTATION.md        # API documentation
├── BOT_SETUP.md                # Telegram bot setup guide
├── templates/                  # HTML templates
│   ├── device-registration.html
│   ├── admin-login.html
│   └── admin-dashboard.html
├── static/                     # Static files (CSS, JS, images)
│   └── style.css
└── telegram_bot/               # Telegram bot
    ├── bot.py                  # Bot implementation
    ├── run.py                  # Bot runner
    ├── __init__.py
    └── requirements.txt        # Bot dependencies
```

## 🔒 Security Features

- Password hashing using Werkzeug security
- Session management with secure cookies
- Input validation and sanitization
- SQL injection protection (parameterized queries)
- CSRF protection
- Secure session timeout

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/devices` | Get all devices |
| GET | `/api/devices/<id>` | Get device by ID |
| GET | `/api/devices/check?name=<name>` | Check if device exists |
| GET | `/api/devices/search?q=<query>` | Search devices |
| GET | `/api/devices/stats` | Get device statistics |
| POST | `/register` | Register a new device |

## 🧪 Development

### Running in Development Mode

```bash
# Set environment variable
export FLASK_ENV=development  # Linux/Mac
set FLASK_ENV=development      # Windows

# Run the app
python app.py
```

### Database Schema

```sql
CREATE TABLE devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    os TEXT,
    browser TEXT,
    ip TEXT,
    registered_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
);
```

## 📝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## 🐛 Troubleshooting

### Bot can't find database
- Make sure `devices.db` exists in the project root
- Check that the bot has read/write permissions

### Bot not responding
- Verify `TELEGRAM_BOT_TOKEN` is set correctly in `.env`
- Check bot token is valid with BotFather
- Review bot logs for errors

### Database locked errors
- SQLite handles concurrent reads
- For heavy usage, consider PostgreSQL or MySQL

### Port already in use
- Change the port in `app.py`: `app.run(host="0.0.0.0", port=8081)`

## 📞 Support

For issues and questions:
- Check the [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- Review [BOT_SETUP.md](./BOT_SETUP.md) for bot-specific issues
- Open an issue on GitHub

## 🙏 Acknowledgments

- Flask - Web framework
- python-telegram-bot - Telegram bot library
- Werkzeug - Security utilities

