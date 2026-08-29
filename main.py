import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()

from scripts.init_db import init_db
from src.bot.keyboards.reply import get_main_menu
from src.bot.handlers.admin import admin_conv
from src.bot.handlers.post import post_conv
from src.bot.handlers.vehicle_handlers import vehicle_conv

# Import your targets safely
from src.bot.handlers.employee_handlers import employee_conv, schedule_handler, open_personal_cabinet
from src.bot.handlers.manager_handlers import manager_handlers, open_manager_cabinet

from src.core.auth_service import is_user_authorized, get_user_role
from scripts.set_admin import seed_admin_user

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("TELEGRAM_CHAT_ID", 0))

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


async def cabinet_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    CRITICAL ROUTER: Intercepts the main cabinet reply-button press 
    and securely routes based on actual real-time database role.
    """
    user_id = update.effective_user.id
    user_role = get_user_role(user_id)

    # Route immediately to manager flow if privileged (Stays out of employee conversation)
    if user_role in ['admin', 'manager', 'owner']:
        await open_manager_cabinet(update, context)
        return

    # Otherwise execute employee menu structure cleanly
    await open_personal_cabinet(update, context)


def main():
    """Start the bot."""
    logger.info("📦 Initializing database...")
    init_db()
    seed_admin_user()

    app = ApplicationBuilder().token(TOKEN).build()
    
    # 1. Global Command Handlers
    app.add_handler(CommandHandler("start", start))

    # 2. Central Router for Reply Keyboard Menus (Takes priority over general text matching)
    app.add_handler(MessageHandler(filters.Text("💼 Личный кабинет"), cabinet_router))

    # 3. Manager/Admin inline response array
    for handler in manager_handlers:
        app.add_handler(handler)

    # 4. Conversations & Sub-workflows
    app.add_handler(employee_conv)
    app.add_handler(schedule_handler)
    app.add_handler(admin_conv)   
    app.add_handler(vehicle_conv) 
    app.add_handler(post_conv) 

    logger.info("🚀 Manul Garage Bot is LIVE (Clean Architecture)")
    app.run_polling()


if __name__ == "__main__":
    main()