#!/usr/bin/env python3
"""
Setup script to create .env file from template
"""

import os
import shutil
from pathlib import Path

def create_env_file():
    """Create .env file from .env.example if it doesn't exist"""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if env_file.exists():
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("Skipping .env file creation.")
            return
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from .env.example")
        print("📝 Please edit .env and add your configuration values!")
    else:
        # Create basic .env file
        env_content = """# Flask Configuration
SECRET_KEY=change-this-to-a-random-secret-key-in-production
FLASK_ENV=development

# Web App URL
WEB_APP_URL=http://localhost:8080

# Telegram Bot Configuration (Optional)
TELEGRAM_BOT_TOKEN=your_bot_token_here
FRONTEND_URL=http://localhost:8080

# Database (optional, defaults to devices.db)
# DB_FILE=devices.db
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ Created .env file with default values")
        print("📝 Please edit .env and add your configuration values!")

if __name__ == "__main__":
    print("=" * 50)
    print("Environment Setup")
    print("=" * 50)
    create_env_file()
    print("=" * 50)

