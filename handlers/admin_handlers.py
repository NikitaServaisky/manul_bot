import os
import logging
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CommandHandler,
    CallbackQueryHandler,
)
from keyboards.reply_keyboards import get_main_menu, get_user_selector_keyboard
from keyboards.inline_keyboards import get_role_selection_keyboard
from core.auth_service import add_user
from dotenv import load_dotenv

load_dotenv()

# Setup logger for this file
logger = logging.getLogger(__name__)

ADDING_USER_FLOW = 1
WAITING_FOR_NAME = 2
ADMIN_ID = int(os.getenv("TELEGRAM_CHAT_ID", 0))


async def start_add_user_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: Admin clicks 'Add employee' and gets the user selector."""
    await update.message.reply_text(
        "Нажмите кнопку ниже, чтобы выбрать сотрудника из списка контактов:",
        reply_markup=get_user_selector_keyboard(),
    )
    return ADDING_USER_FLOW


async def process_user_shared(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: User is selected. Extracting ID from PTB Object."""
    shared_data = update.message.users_shared or update.message.user_shared
    target_id = None

    if shared_data:
        if hasattr(shared_data, "users") and shared_data.users:
            target_id = shared_data.users[0].user_id
        elif shared_data.api_kwargs and "user_ids" in shared_data.api_kwargs:
            target_id = shared_data.api_kwargs["user_ids"][0]
        elif hasattr(shared_data, "user_id"):
            target_id = shared_data.user_id

    if not target_id:
        await update.message.reply_text("❌ Ошибка: Не удалось получить ID.")
        return ADDING_USER_FLOW

    context.user_data["pending_id"] = target_id

    await update.message.reply_text(
        f"✅ Пользователь выбран (ID: {target_id}).\n"
        "📝 Введите ИМЯ и ФАМИЛИЮ сотрудника:"
    )
    return WAITING_FOR_NAME


async def process_user_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 3: Name raceived. Now ask for role."""
    user_name = update.message.text
    target_id = context.user_data.get("pending_id")

    # Save name in memory
    context.user_data["pending_name"] = user_name

    await update.message.reply_text(
        f"Сотрудник: {user_name}\n"
        "Какую роль ему назначить?",
        reply_markup=get_role_selection_keyboard(target_id),
    )
    return ADDING_USER_FLOW


async def handel_role_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 4: Save user to DB."""
    query = update.callback_query
    admin_id = update.effective_user.id
    await query.answer()

    data = query.data.split("_")
    if data[0] != "setrole":
        return

    target_id = int(data[1])
    role = data[2]
    full_name = context.user_data.get("pending_name", f"user_{target_id}")

    # Debuging print
    logger.info(f"DEBUG: Attempting to add user {target_id} that is called {full_name} with role {role}")

    try:
        add_user(user_id=target_id, username=full_name, role=role)
        logger.info(f"DEBUG: Successfully added user {target_id}, {full_name}, {role} to DB")
        await query.edit_message_text(
            f"✅ Сотрудник {full_name} добавлен как {role}!"
        )
    except Exception as e:
        logger.exception(f"❌ DATABASE ERROR: {e}")
        await query.edit_message_text(f"❌ Ошибка сохранения.")

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Возврат в главное меню... 🛠️",
        reply_markup=get_main_menu(admin_id, ADMIN_ID, "owner"),
    )
    return ConversationHandler.END


async def cancel_admin_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the process."""
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text("❌ Действие отменено.")
    else:
        await update.message.reply_text("❌ Действие отменено.")

    admin_id = update.effective_user.id
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Чем еще могу помочь? 🛠️",
        reply_markup=get_main_menu(admin_id, ADMIN_ID, "owner"),
    )
    return ConversationHandler.END


admin_conv = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex("^➕ Добавить сотрудника$"), start_add_user_flow)
    ],
    states={
        ADDING_USER_FLOW: [
            MessageHandler(filters.StatusUpdate.USERS_SHARED, process_user_shared),
            CallbackQueryHandler(handel_role_callback, pattern="^setrole_"),
            CallbackQueryHandler(cancel_admin_flow, pattern="^cancel_admin$"),
        ],
        WAITING_FOR_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_user_name),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_admin_flow)],
)
