import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

# CRITICAL: Load environment variables BEFORE importing internal modules
load_dotenv()

# Now it's safe to import database and internal handlers
from scripts.init_db import init_db
from keyboards.reply_keyboards import get_main_menu
from handlers.admin_handlers import admin_conv
from handlers.post_handlers import post_conv
from handlers.vehicle_handlers import vehicle_conv
from handlers.employee_handlers import employee_conv, schedule_handler

from core.auth_service import is_user_authorized, get_user_role
from scripts.set_admin import seed_admin_user

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
    message = update.effective_message
    if not message:
        return

    authorized = (user_id == ADMIN_ID) or is_user_authorized(user_id)

    if not authorized:
        await message.reply_text("❌ Нет доступа. Обратитесь к администратору.")
        return

    await message.reply_text(
        "🛠️ Добро пожаловать в Manul Garage!",
        reply_markup=get_main_menu(user_id),
    )


def main():
    """Start the bot."""
    logger.info("📦 Initializing database...")
    init_db()
    seed_admin_user()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(admin_conv)   
    app.add_handler(vehicle_conv) 
    app.add_handler(post_conv) 
    app.add_handler(employee_conv)
    app.add_handler(schedule_handler)   

    logger.info("🚀 Manul Garage Bot is LIVE (Clean Architecture)")
    app.run_polling()


if __name__ == "__main__":
    main()