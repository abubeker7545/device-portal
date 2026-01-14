import os
import sys
import logging
import asyncio
from typing import Optional
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from telegram.error import TimedOut, NetworkError
from telegram.request import HTTPXRequest
import sqlite3

# Add parent directory to path to import app functions
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_DEVICE_NAME = 1
WAITING_FOR_SERIAL_NUMBER = 2

class TelegramBot:
    def __init__(self, db_file=None, web_app_url=None):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.webhook_url = os.getenv('TELEGRAM_WEBHOOK_URL')
        self.webhook_secret = os.getenv('TELEGRAM_WEBHOOK_SECRET')
        self.web_app_url = web_app_url or os.getenv('FRONTEND_URL', 'http://localhost:8080')
        
        # Resolve database file path
        if db_file is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.db_file = os.path.join(project_root, "devices.db")
        else:
            if not os.path.isabs(db_file):
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                self.db_file = os.path.join(project_root, db_file)
            else:
                self.db_file = db_file
        
        # Verify database file exists or can be created
        try:
            conn = sqlite3.connect(self.db_file)
            conn.close()
            logger.info(f"Database connection verified: {self.db_file}")
        except Exception as e:
            logger.warning(f"Database file not accessible: {self.db_file}. Error: {e}")
            logger.warning("Bot will attempt to create database on first use.")
        
        # Resolve the logo path
        self.logo_path = os.path.join(os.path.dirname(__file__), 'repari.png')
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        
        # Configure request with longer timeout for file uploads
        request = HTTPXRequest(
            connection_pool_size=8,
            read_timeout=30.0,  # 30 seconds for reading responses
            write_timeout=30.0,  # 30 seconds for sending requests
            connect_timeout=10.0,  # 10 seconds for connection
        )
        
        self.application = Application.builder().token(self.bot_token).request(request).build()
        self._setup_handlers()
        logger.info("Bot handlers setup complete")
    
    def _is_https(self, url):
        """Check if URL is HTTPS (required for Telegram Web App buttons)"""
        return url and url.lower().startswith('https://')
    
    def _is_embeddable_domain(self, url: Optional[str]) -> bool:
        """Return False for domains known to disallow embedding in iframes/webviews."""
        if not url:
            return False
        try:
            from urllib.parse import urlparse
            hostname = urlparse(url).hostname or ''
        except Exception:
            return False
        hostname = hostname.lower()
        blocked = {
            'github.com',
            'www.github.com',
            'github.io',
        }
        if hostname in blocked or hostname.endswith('.github.io'):
            return False
        return True
    
    def _create_web_app_button(self, text, url):
        """Create a web app button only if URL is HTTPS, otherwise return None"""
        if self._is_https(url) and self._is_embeddable_domain(url):
            return InlineKeyboardButton(text, web_app=WebAppInfo(url=url))
        return None
    
    def _setup_handlers(self):
        """Set up command and message handlers"""
        # Conversation handler for device registration
        register_conv = ConversationHandler(
            entry_points=[CommandHandler("register", self.register_command)],
            states={
                WAITING_FOR_DEVICE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.register_device_name)],
                WAITING_FOR_SERIAL_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.register_serial_number)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_command)],
        )
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("app", self.open_app_command))
        self.application.add_handler(CommandHandler("devices", self.devices_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(register_conv)
        
        # Callback query handler for buttons
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        web_portal_info = ""
        if not self._is_https(self.web_app_url):
            web_portal_info = f"\n\n🌐 Web Portal: {self.web_app_url}\n(Use /app to get the link)"
        
        welcome_text = (
            f"👋 Welcome {user.first_name}!\n\n"
            f"<b>Device Registration Portal</b>\n\n"
            f"I can help you:\n"
            f"• Register your device\n"
            f"• View registered devices\n"
            f"• Check device statistics\n"
            f"• Access the web portal{web_portal_info}\n\n"
            f"Use /help to see all available commands."
        )
        
        # Build keyboard
        keyboard = []
        web_app_btn = self._create_web_app_button("🌐 Open Web Portal", self.web_app_url)
        if web_app_btn:
            keyboard.append([web_app_btn])
        else:
            keyboard.append([InlineKeyboardButton("🔗 Web Portal Link", url=self.web_app_url)])
        
        keyboard.extend([
            [InlineKeyboardButton("📱 Register Device", callback_data="register")],
            [InlineKeyboardButton("📊 View Devices", callback_data="devices")],
        ])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Try to send logo, fallback to text on timeout or file errors
        try:
            with open(self.logo_path, 'rb') as logo_file:
                try:
                    await asyncio.wait_for(
                        update.message.reply_photo(
                            photo=logo_file,
                            caption=welcome_text,
                            reply_markup=reply_markup,
                            parse_mode='HTML'
                        ),
                        timeout=25.0  # 25 second timeout for photo upload
                    )
                except (TimedOut, NetworkError, asyncio.TimeoutError) as e:
                    logger.warning(f"Timeout or network error sending photo: {e}. Falling back to text message.")
                    await update.message.reply_text(
                        welcome_text,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
        except FileNotFoundError:
            logger.warning(f"Logo file not found: {self.logo_path}. Sending text message.")
            await update.message.reply_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Unexpected error sending photo: {e}. Falling back to text message.")
            await update.message.reply_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "🤖 <b>Bot Commands:</b>\n\n"
            "/start - Start the bot and see main menu\n"
            "/register - Register your device\n"
            "/devices - View all registered devices\n"
            "/stats - View device statistics\n"
            "/app - Get web portal link\n"
            "/help - Show this help message\n\n"
            "💡 <b>Quick Tips:</b>\n"
            "• Use /register to add your device\n"
            "• Your OS and browser will be detected automatically\n"
            "• Use /devices to see all registered devices\n"
            "• Use /app to get the web portal link"
        )
        
        keyboard = []
        web_app_btn = self._create_web_app_button("🌐 Open Web Portal", self.web_app_url)
        if web_app_btn:
            keyboard.append([web_app_btn])
        else:
            keyboard.append([InlineKeyboardButton("🔗 Web Portal Link", url=self.web_app_url)])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            help_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def open_app_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /app command to open the web portal"""
        keyboard = []
        web_app_btn = self._create_web_app_button("🌐 Open Web Portal", self.web_app_url)
        
        if web_app_btn:
            keyboard.append([web_app_btn])
            message_text = "Click the button below to open the device registration portal:"
        else:
            keyboard.append([InlineKeyboardButton("🔗 Open Web Portal", url=self.web_app_url)])
            message_text = (
                f"Click the button below to open the device registration portal:\n\n"
                f"Or copy this link: {self.web_app_url}\n\n"
                f"Note: For Mini App support, use HTTPS in production."
            )
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup
        )
    
    async def register_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /register command"""
        await update.message.reply_text(
            "📱 <b>Device Registration</b>\n\n"
            "Please send me the name for your device (e.g., 'My iPhone', 'Office Laptop').\n\n"
            "Your operating system and browser will be detected automatically.\n"
            "Type /cancel to cancel.",
            parse_mode='HTML'
        )
        return WAITING_FOR_DEVICE_NAME
    
    async def register_device_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle device name input for registration"""
        device_name = update.message.text.strip()
        
        # Validate device name
        if not device_name or len(device_name) > 100:
            await update.message.reply_text(
                "❌ Invalid device name. Please provide a name (max 100 characters).\n"
                "Type /cancel to cancel."
            )
            return WAITING_FOR_DEVICE_NAME
        
        context.user_data['device_name'] = device_name
        
        await update.message.reply_text(
            f"Great! Now please send me the <b>Serial Number</b> for '{device_name}'.\n\n"
            "This is usually a unique identifier for your device.",
            parse_mode='HTML'
        )
        return WAITING_FOR_SERIAL_NUMBER

    async def register_serial_number(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle serial number input for registration"""
        serial_number = update.message.text.strip()
        device_name = context.user_data.get('device_name')
        
        if not serial_number or len(serial_number) > 100:
            await update.message.reply_text(
                "❌ Invalid serial number. Please provide a valid serial number (max 100 characters).\n"
                "Type /cancel to cancel."
            )
            return WAITING_FOR_SERIAL_NUMBER
        
        # Detect OS and Browser from user agent
        os_name = "Telegram"
        browser = "Telegram Bot"
        ip = "N/A"
        
        # Register device in database
        try:
            with sqlite3.connect(self.db_file) as conn:
                # Check if serial number already exists
                cur = conn.cursor()
                cur.execute("SELECT id FROM devices WHERE serial_number = ?", (serial_number,))
                if cur.fetchone():
                    await update.message.reply_text(
                        f"❌ Serial number <code>{serial_number}</code> is already registered.\n"
                        "Please provide a different serial number or type /cancel.",
                        parse_mode='HTML'
                    )
                    return WAITING_FOR_SERIAL_NUMBER

                conn.execute(
                    "INSERT INTO devices (name, serial_number, os, browser, ip, is_authorized) VALUES (?, ?, ?, ?, ?, 0)",
                    (device_name, serial_number, os_name, browser, ip)
                )
                conn.commit()
            
            logger.info(f"Device registered via bot: {device_name} (SN: {serial_number})")
            await update.message.reply_text(
                f"✅ <b>Device Registered Successfully!</b>\n\n"
                f"Device Name: {device_name}\n"
                f"Serial Number: {serial_number}\n"
                f"OS: {os_name}\n"
                f"Browser: {browser}\n\n"
                f"Your device has been registered and is awaiting admin authorization.",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error registering device: {e}")
            await update.message.reply_text(
                "❌ An error occurred while registering your device. Please try again later."
            )
        
        return ConversationHandler.END
    
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the current conversation"""
        await update.message.reply_text("❌ Registration cancelled.")
        return ConversationHandler.END
    
    async def devices_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /devices command to list all devices"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, name, os, browser, ip, registered_at FROM devices ORDER BY id DESC LIMIT 20")
                devices = cur.fetchall()
            
            if not devices:
                await update.message.reply_text("📱 No devices registered yet.")
                return
            
            text = "📱 <b>Registered Devices</b>\n\n"
            for device in devices:
                device_id, name, os_name, browser, ip, registered_at = device
                text += (
                    f"🆔 ID: {device_id}\n"
                    f"📛 Name: {name}\n"
                    f"💻 OS: {os_name}\n"
                    f"🌐 Browser: {browser}\n"
                    f"📍 IP: {ip}\n"
                    f"📅 Registered: {registered_at}\n\n"
                )
            
            # Split message if too long
            if len(text) > 4096:
                chunks = [text[i:i+4096] for i in range(0, len(text), 4096)]
                for chunk in chunks:
                    await update.message.reply_text(chunk, parse_mode='HTML')
            else:
                await update.message.reply_text(text, parse_mode='HTML')
                
        except Exception as e:
            logger.error(f"Error fetching devices: {e}")
            await update.message.reply_text("❌ An error occurred while fetching devices.")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command to show device statistics"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cur = conn.cursor()
                
                # Total devices
                cur.execute("SELECT COUNT(*) FROM devices")
                total = cur.fetchone()[0]
                
                # Devices by OS
                cur.execute("SELECT os, COUNT(*) FROM devices GROUP BY os")
                os_stats = cur.fetchall()
                
                # Devices by browser
                cur.execute("SELECT browser, COUNT(*) FROM devices GROUP BY browser")
                browser_stats = cur.fetchall()
            
            text = "📊 <b>Device Statistics</b>\n\n"
            text += f"📱 Total Devices: {total}\n\n"
            
            if os_stats:
                text += "<b>By Operating System:</b>\n"
                for os_name, count in os_stats:
                    text += f"  • {os_name}: {count}\n"
                text += "\n"
            
            if browser_stats:
                text += "<b>By Browser:</b>\n"
                for browser, count in browser_stats:
                    text += f"  • {browser}: {count}\n"
            
            await update.message.reply_text(text, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error fetching stats: {e}")
            await update.message.reply_text("❌ An error occurred while fetching statistics.")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages"""
        user_message = update.message.text.lower()
        
        if any(word in user_message for word in ['register', 'add device', 'new device']):
            response = "📱 Use /register to register your device!"
        elif any(word in user_message for word in ['devices', 'list', 'show devices']):
            response = "📱 Use /devices to view all registered devices!"
        elif any(word in user_message for word in ['stats', 'statistics', 'count']):
            response = "📊 Use /stats to view device statistics!"
        elif any(word in user_message for word in ['help', 'support', 'commands']):
            response = "❓ Use /help to see all available commands!"
        else:
            response = (
                "👋 I'm here to help with device registration!\n\n"
                "Use /help to see all commands or /register to register a device."
            )
        
        # Build keyboard
        keyboard = []
        web_app_btn = self._create_web_app_button("🌐 Open Web Portal", self.web_app_url)
        if web_app_btn:
            keyboard.append([web_app_btn])
        else:
            keyboard.append([InlineKeyboardButton("🔗 Web Portal Link", url=self.web_app_url)])
        
        keyboard.extend([
            [InlineKeyboardButton("📱 Register Device", callback_data="register")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
        ])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            response,
            reply_markup=reply_markup
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "register":
            await query.edit_message_text(
                "📱 <b>Device Registration</b>\n\n"
                "Please send me the name for your device (e.g., 'My iPhone', 'Office Laptop').\n\n"
                "Your operating system and browser will be detected automatically.\n"
                "Type /cancel to cancel.",
                parse_mode='HTML'
            )
            context.user_data['state'] = WAITING_FOR_DEVICE_NAME
        elif query.data == "devices":
            # Fetch and display devices
            try:
                with sqlite3.connect(self.db_file) as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT id, name, os, browser, ip, registered_at FROM devices ORDER BY id DESC LIMIT 10")
                    devices = cur.fetchall()
                
                if not devices:
                    await query.edit_message_text("📱 No devices registered yet.")
                    return
                
                text = "📱 <b>Recent Registered Devices</b>\n\n"
                for device in devices:
                    device_id, name, os_name, browser, ip, registered_at = device
                    text += (
                        f"🆔 {device_id}: {name}\n"
                        f"   💻 {os_name} | 🌐 {browser}\n\n"
                    )
                
                await query.edit_message_text(text, parse_mode='HTML')
            except Exception as e:
                logger.error(f"Error fetching devices: {e}")
                await query.edit_message_text("❌ An error occurred while fetching devices.")
        elif query.data == "help":
            await self.help_command(update, context)
        elif query.data == "main_menu":
            await self.start_command(update, context)
    
    async def webhook_handler(self, request):
        """Handle incoming webhook requests - for use with webhook_server.py"""
        try:
            # Parse the incoming update
            update_data = await request.json()
            update = Update.de_json(update_data, self.application.bot)
            
            # Process the update
            await self.application.process_update(update)
            
            return {"status": "ok"}
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return {"status": "error", "message": str(e)}
    
    async def set_webhook(self):
        """Set the webhook URL for the bot"""
        if self.webhook_url:
            webhook_url = f"{self.webhook_url}/webhook"
            secret_token = self.webhook_secret
            
            await self.application.bot.set_webhook(
                url=webhook_url,
                secret_token=secret_token,
                drop_pending_updates=True
            )
            logger.info(f"Webhook set to: {webhook_url}")
            
            # Verify webhook info
            webhook_info = await self.application.bot.get_webhook_info()
            logger.info(f"Webhook info: {webhook_info.to_dict()}")
        else:
            logger.warning("No webhook URL configured. Bot will use polling mode.")
    
    async def delete_webhook(self):
        """Delete the webhook (use for polling mode)"""
        await self.application.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook deleted - bot running in polling mode")
    
    def run_polling(self):
        """Start the bot in polling mode using the v20+ run_polling API"""
        logger.info("=" * 60)
        logger.info("🚀 Starting Telegram Bot in polling mode...")
        logger.info(f"📁 Database: {self.db_file}")
        logger.info(f"🌐 Web App URL: {self.web_app_url}")
        logger.info("=" * 60)
        
        # This handles initialize/start/polling/idle/shutdown internally
        self.application.run_polling()

def main():
    """Main function to run the bot standalone"""
    try:
        print("=" * 60)
        print("🚀 Telegram Bot - Device Registration Portal")
        print("=" * 60)
        print("Initializing bot...")
        
        bot = TelegramBot()
        
        print(f"✅ Bot initialized successfully")
        print(f"📁 Database: {bot.db_file}")
        print(f"🌐 Web App URL: {bot.web_app_url}")
        print("=" * 60)
        print("\nStarting bot in polling mode...")
        print("Press Ctrl+C to stop the bot\n")
        
        # Always use polling mode when run directly (synchronous)
        bot.run_polling()
            
    except KeyboardInterrupt:
        print("\n\nBot stopped by user")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        print(f"\n❌ Error: {e}")
        raise

if __name__ == "__main__":
    main()