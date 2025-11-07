import os
import sys
from dotenv import load_dotenv

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from webhook_server import WebhookServer

# Create server instance
server = WebhookServer()
application = server.app  # for cPanel Passenger

if __name__ == "__main__":
    port = int(os.environ.get("WEBHOOK_PORT", 8081))
    print("=" * 60)
    print("🤖 Starting Telegram Webhook Server")
    print("=" * 60)
    server.run()
