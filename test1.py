import logging
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE_URL = "https://api.your-service.com/check"   # CHANGE THIS

USER_DB = {}
STATE = {}

def get_user(user_id):
    if user_id not in USER_DB:
        USER_DB[user_id] = {
            "registered": True,
            "free_calls": 10,
            "paid_calls": 0
        }
    return USER_DB[user_id]


# ---------------- MAIN MENU ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Welcome to **Mobile Device Check Bot**.\nChoose an option:"
    buttons = [
        [InlineKeyboardButton("🛠️ Services", callback_data="services")],
        [InlineKeyboardButton("👤 Account", callback_data="account")],
        [InlineKeyboardButton("ℹ️ Info", callback_data="info")],
        [InlineKeyboardButton("🆘 Help", callback_data="help")],
        [InlineKeyboardButton("💸 Refund", callback_data="refund")],
    ]
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )


# ---------------- CALLBACK HANDLER ---------------- #

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    data = query.data

    # BACK BUTTON
    if data == "back_main":
        await start(update, context)
        return

    # INFO
    if data == "info":
        await query.edit_message_text("This bot provides legal mobile device lookup services.")
        return

    # HELP
    if data == "help":
        await query.edit_message_text("Use /start to open the menu. Contact admin for support.")
        return

    # ACCOUNT
    if data == "account":
        user = get_user(user_id)
        msg = (
            f"👤 **Account Details**\n"
            f"Free API calls left: {user['free_calls']}\n"
            f"Paid API calls used: {user['paid_calls']}"
        )
        await query.edit_message_text(msg)
        return

    # REFUND
    if data == "refund":
        await query.edit_message_text("Refund request submitted. Our team will review soon.")
        return

    # SERVICE LIST
    if data == "services":
        buttons = [
            [InlineKeyboardButton("📱 Apple Services", callback_data="grp_apple")],
            [InlineKeyboardButton("📱 Samsung Services", callback_data="grp_samsung")],
            [InlineKeyboardButton("🌍 Global Services", callback_data="grp_global")],
            [InlineKeyboardButton("⬅️ Back", callback_data="back_main")],
        ]
        await query.edit_message_text("Choose a service category:", reply_markup=InlineKeyboardMarkup(buttons))
        return

    # APPLE GROUP
    if data == "grp_apple":
        buttons = [
            [InlineKeyboardButton("Apple Warranty Check", callback_data="svc_apple_warranty")],
            [InlineKeyboardButton("Coverage Status", callback_data="svc_apple_coverage")],
            [InlineKeyboardButton("Apple Model Info", callback_data="svc_apple_model")],
            [InlineKeyboardButton("Apple Specs", callback_data="svc_apple_specs")],
            [InlineKeyboardButton("Activation Status", callback_data="svc_apple_activation")],
            [InlineKeyboardButton("⬅️ Back", callback_data="services")],
        ]
        await query.edit_message_text("📱 **Apple Services**", reply_markup=InlineKeyboardMarkup(buttons))
        return

    # SAMSUNG GROUP
    if data == "grp_samsung":
        buttons = [
            [InlineKeyboardButton("Samsung Warranty", callback_data="svc_sam_warranty")],
            [InlineKeyboardButton("Samsung Model Info", callback_data="svc_sam_model")],
            [InlineKeyboardButton("Carrier Lookup", callback_data="svc_sam_carrier")],
            [InlineKeyboardButton("⬅️ Back", callback_data="services")],
        ]
        await query.edit_message_text("📱 **Samsung Services**", reply_markup=InlineKeyboardMarkup(buttons))
        return

    # GLOBAL GROUP
    if data == "grp_global":
        buttons = [
            [InlineKeyboardButton("GSMA Blacklist", callback_data="svc_blacklist")],
            [InlineKeyboardButton("Brand Detector", callback_data="svc_brand")],
            [InlineKeyboardButton("Android Model Lookup", callback_data="svc_android_model")],
            [InlineKeyboardButton("IMEI Basic Lookup", callback_data="svc_imei_basic")],
            [InlineKeyboardButton("Serial Number Lookup", callback_data="svc_serial")],
            [InlineKeyboardButton("Network Carrier Info", callback_data="svc_carrier")],
            [InlineKeyboardButton("Hardware Specs", callback_data="svc_specs")],
            [InlineKeyboardButton("⬅️ Back", callback_data="services")],
        ]
        await query.edit_message_text("🌍 **Global Services**", reply_markup=InlineKeyboardMarkup(buttons))
        return

    # ANY SERVICE SELECTED → ASK IMEI
    if data.startswith("svc_"):
        STATE[user_id] = {"awaiting_imei": True, "service": data}
        await query.edit_message_text("Send the IMEI or Serial Number for this service:")
        return


# ---------------- IMEI PROCESSOR ---------------- #

async def receive_imei(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in STATE or not STATE[user_id]["awaiting_imei"]:
        return

    imei = update.message.text.strip()
    service = STATE[user_id]["service"]
    user = get_user(user_id)

    # QUOTA CHECK
    if user["free_calls"] <= 0:
        await update.message.reply_text("❌ You have no free API calls left.")
        return

    # ---------------- REAL API CALL ----------------
    try:
        response = requests.get(f"{API_BASE_URL}/{service}", params={"imei": imei}, timeout=10)
        result = response.json()
    except:
        await update.message.reply_text("API error. Try again.")
        return

    # DECREASE FREE USAGE
    user["free_calls"] -= 1

    await update.message.reply_text(
        f"Service: {service}\nIMEI: {imei}\n\nResult:\n{result}"
    )

    STATE[user_id]["awaiting_imei"] = False


# ---------------- MAIN ---------------- #

def main():
    app = Application.builder().token("6806239673:AAESKUzLKgyOWl0-atsgsA-diSYrkhmRO9I").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_imei))

    app.run_polling()


if __name__ == "__main__":
    main()
