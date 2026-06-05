import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
from scripts.init_db import init_db

# Internal Imports - Bringing everything together
from keyboards.reply_keyboards import get_main_menu
from handlers.admin_handlers import admin_conv
from handlers.post_handlers import post_conv
from handlers.vehicle_handlers import vehicle_conv
from core.auth_service import is_user_authorized, get_user_role

# Load Environment Variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("TELEGRAM_CHAT_ID", 0))

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point: Checks authorization and shows the correct menu."""
    user_id = update.effective_user.id
    
    # Use effective_message to handle both text messages and callbacks safely
    message = update.effective_message
    if not message:
        return

    # 1. Security Check
    authorized = (user_id == ADMIN_ID) or is_user_authorized(user_id)

    if not authorized:
        await message.reply_text("❌ Нет доступа. Обратитесь к администратору.")
        return

    # 2. Get Role from DB
    role = "owner" if user_id == ADMIN_ID else get_user_role(user_id)

    # 3. Show Menu
    await message.reply_text(
        "🛠️ Добро пожаловать в Manul Garage!",
        reply_markup=get_main_menu(user_id),
    )


def main():
    """Start the bot."""
    logger.info("📦 Initializing database...")
    init_db()

    # Create the application
    app = ApplicationBuilder().token(TOKEN).build()

    # Register Handlers
    app.add_handler(CommandHandler("start", start))

    # The Modular Handlers we built
    app.add_handler(admin_conv)  # Employee management flow
    app.add_handler(vehicle_conv) # Vehicle & Customer management flow
    app.add_handler(post_conv)   # AI Post creation flow

    logger.info("🚀 Manul Garage Bot is LIVE (Clean Architecture)")
    app.run_polling()


if __name__ == "__main__":
    main()