import os
import logging
import asyncio
import threading
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from telegram import Update
from telegram_bot.bot import TelegramBot

load_dotenv()
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webhook")

bot_instance = TelegramBot()

# Create background asyncio loop
loop = asyncio.new_event_loop()

def start_loop():
    asyncio.set_event_loop(loop)
    loop.run_forever()

threading.Thread(target=start_loop, daemon=True).start()

# Start bot in that loop
async def start_bot():
    await bot_instance.application.initialize()
    await bot_instance.application.start()

asyncio.run_coroutine_threadsafe(start_bot(), loop)

# Webhook route
@app.route("/webhook", methods=["POST"])
def handle_webhook():
    try:
        # Verify Telegram secret
        expected_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET")
        provided_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if expected_secret and expected_secret != provided_secret:
            logger.warning("Invalid webhook secret")
            return jsonify({"error": "Forbidden"}), 403

        data = request.get_json(force=True)
        update = Update.de_json(data, bot_instance.application.bot)

        # Run process_update in background loop
        asyncio.run_coroutine_threadsafe(
            bot_instance.application.process_update(update), loop
        )

        # Immediately return 200 OK to Telegram
        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "telegram-bot-webhook"
    })

# Required for cPanel Passenger
application = app

if __name__ == "__main__":
    port = int(os.environ.get("WEBHOOK_PORT", 8081))
    app.run(host="0.0.0.0", port=port)
