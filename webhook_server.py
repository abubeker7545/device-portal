import os
import logging
import asyncio
from aiohttp import web
from telegram import Update
from telegram_bot.bot import TelegramBot

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class WebhookServer:
    def __init__(self):
        self.bot = TelegramBot()
        self.app = web.Application()
        self.setup_routes()
    
    def setup_routes(self):
        """Setup web routes"""
        self.app.router.add_post('/webhook', self.handle_webhook)
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/', self.root_handler)
    
    async def handle_webhook(self, request):
        """Handle incoming Telegram webhook requests"""
        try:
            # Verify secret token if set
            expected_secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET")
            if expected_secret:
                provided_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
                if provided_secret != expected_secret:
                    logger.warning(f"Invalid webhook secret: {provided_secret}")
                    return web.json_response({"error": "Forbidden"}, status=403)
            
            # Parse the update
            data = await request.json()
            logger.info(f"Received webhook update: {data.get('update_id', 'unknown')}")
            
            # Process the update
            update = Update.de_json(data, self.bot.application.bot)
            await self.bot.application.process_update(update)
            
            return web.json_response({"status": "ok"})
        
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def health_check(self, request):
        """Health check endpoint"""
        return web.json_response({
            "status": "healthy", 
            "service": "telegram-bot-webhook",
            "bot_username": (await self.bot.application.bot.get_me()).username
        })
    
    async def root_handler(self, request):
        """Root endpoint"""
        return web.json_response({
            "message": "Telegram Bot Webhook Server",
            "endpoints": {
                "webhook": "POST /webhook",
                "health": "GET /health"
            }
        })
    
    async def on_startup(self, app):
        """Run on server startup"""
        logger.info("Starting webhook server...")
        
        # Set webhook URL
        webhook_url = os.environ.get("TELEGRAM_WEBHOOK_URL")
        if webhook_url:
            full_webhook_url = f"{webhook_url}/webhook"
            secret_token = os.environ.get("TELEGRAM_WEBHOOK_SECRET")
            
            await self.bot.application.bot.set_webhook(
                url=full_webhook_url,
                secret_token=secret_token,
                drop_pending_updates=True
            )
            logger.info(f"Webhook set to: {full_webhook_url}")
            
            # Verify webhook info
            webhook_info = await self.bot.application.bot.get_webhook_info()
            logger.info(f"Webhook info: {webhook_info.to_dict()}")
        else:
            logger.warning("No TELEGRAM_WEBHOOK_URL set. Webhook not configured.")
    
    async def on_shutdown(self, app):
        """Run on server shutdown"""
        logger.info("Shutting down webhook server...")
        await self.bot.application.shutdown()
    
    def run(self):
        """Start the webhook server"""
        port = int(os.environ.get('WEBHOOK_PORT', 8081))
        
        # Add startup and shutdown hooks
        self.app.on_startup.append(self.on_startup)
        self.app.on_shutdown.append(self.on_shutdown)
        
        logger.info("=" * 60)
        logger.info("🚀 Starting Telegram Bot Webhook Server")
        logger.info(f"📍 Port: {port}")
        logger.info(f"🌐 Webhook URL: {os.environ.get('TELEGRAM_WEBHOOK_URL', 'Not set')}")
        logger.info("=" * 60)
        
        web.run_app(
            self.app,
            host='0.0.0.0',
            port=port,
            access_log=None  # Disable aiohttp access logs to reduce noise
        )

if __name__ == "__main__":
    server = WebhookServer()
    server.run()