import os
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from dotenv import load_dotenv

# Internal Imports - Bringing everything together
from keyboards.reply_keyboards import get_main_menu
from handlers.admin_handlers import admin_conv, handel_role_callback
from handlers.post_handlers import post_conv
from core.auth_service import is_user_authorized, get_user_role

# Load Environment Variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update, context):
    """Entry point: Checks authorization and shows the correct menu."""
    user_id = update.effective_user.id
    
    # 1. Security Check
    authorized = (user_id == ADMIN_ID) or is_user_authorized(user_id)
    
    if not authorized:
        await update.message.reply_text("❌ Нет доступа. Обратитесь к администратору.")
        return

    # 2. Get Role from DB
    role = "owner" if user_id == ADMIN_ID else get_user_role(user_id)
    
    # 3. Show Menu
    await update.message.reply_text(
        "🛠️ Добро пожаловать в Manul Garage!",
        reply_markup=get_main_menu(user_id, ADMIN_ID, role)
    )

def main():
    """Start the bot."""
    # Create the application
    app = ApplicationBuilder().token(TOKEN).build()

    # Register Handlers
    app.add_handler(CommandHandler("start", start))
    
    # The Modular Handlers we built
    app.add_handler(admin_conv)  # Employee management flow
    app.add_handler(post_conv)   # AI Post creation flowed

    print("🚀 Manul Garage Bot is LIVE (Clean Architecture)")
    app.run_polling()

if __name__ == "__main__":
    main()