#!/usr/bin/env python3
"""
Simple script to run the Telegram bot separately from the Flask app
Supports both polling and webhook modes
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to load .env from project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from project root
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    # Also try loading from telegram_bot directory
    load_dotenv()

def main():
    parser = argparse.ArgumentParser(description='Run the Telegram bot for Device Registration Portal')
    parser.add_argument('--mode', choices=['polling', 'webhook'], default='polling',
                       help='Run mode: polling (default) or webhook')
    parser.add_argument('--host', default='0.0.0.0',
                       help='Host for webhook server (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000,
                       help='Port for webhook server (default: 8000)')
    
    args = parser.parse_args()
    
    if args.mode == 'polling':
        print("=" * 60)
        print("🚀 Telegram Bot - Device Registration Portal")
        print("=" * 60)
        print("Starting bot in polling mode...")
        print(f"Database: {project_root / 'devices.db'}")
        print(f"Web App URL: {os.getenv('WEB_APP_URL', 'http://localhost:8080')}")
        print("=" * 60)
        print("\nBot Commands:")
        print("  /start - Welcome message")
        print("  /register - Register a device")
        print("  /devices - View registered devices")
        print("  /stats - View statistics")
        print("  /app - Open web portal")
        print("  /help - Show help")
        print("=" * 60)
        print("\nPress Ctrl+C to stop the bot\n")
        
        try:
            from bot import TelegramBot
            bot = TelegramBot()
            asyncio.run(bot.start_polling())
        except KeyboardInterrupt:
            print("\n\nBot stopped by user")
        except Exception as e:
            print(f"\n❌ Error starting bot: {e}")
            sys.exit(1)
    else:
        print(f"🌐 Webhook mode not yet implemented")
        print(f"Use polling mode for now: python run.py --mode polling")
        sys.exit(1)

if __name__ == "__main__":
    main()
