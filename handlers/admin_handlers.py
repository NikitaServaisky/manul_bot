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
from core.auth_service import add_user, is_user_authorized
from dotenv import load_dotenv
import os

load_dotenv()

# State for the ConversationHandler
ADDING_USER_FLOW = 1
ADMIN_ID = int(os.getenv("TELEGRAM_CHAT_ID", 0))

async def start_add_user_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: Admin clicks 'Add employee' and gets the user selector."""
    await update.message.reply_text(
        "Нажмите кнопку ниже, чтобы выбрать сотрудника из списка контактов:",
        reply_markup=get_user_selector_keyboard()
    )
    return ADDING_USER_FLOW

async def process_user_shared(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Step 2: User is selected. Ask for their role (Mechanic/Owner)."""
    shared_data = update.message.users_shared or update.message.user_shared
    # Debuging print
    print(f"DEBUG FULL OBJECT: {shared_data}")

    target_id = None
    if shared_data:
        if hasattr(shared_data, 'user_ids') and shared_data.user_ids:
            target_id = shared_data.user_ids[0]
        elif hasattr(shared_data, 'user_id'):
            target_id = shared_data.user_id

    if not target_id:
        # Debuging print
        print(f"FAILED TO GET ID. Update contents: {update.message.to_dict()}")
        await update.message.reply_text("❌ Ошибка выбора. Попробуйте еще раз.")
        return ADDING_USER_FLOW

    # Debuging print
    print(f"DEBUG: Selected User ID is {target_id}")

    await update.message.reply_text(
        f"Пользователь выбран (ID: {target_id}). Какую роль ему назначить?",
        reply_markup=get_role_selection_keyboard(target_id)
    )
    return ADDING_USER_FLOW

async def handel_role_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 3: Admin clicks a role button."""
    query = update.callback_query
    admin_id = update.effective_user.id
    await query.answer()

    data = query.data.split("_")
    if data[0] != "setrole":
        return

    target_id = int(data[1])
    role = data[2]

    add_user(target_id, role=role)

    await query.edit_message_text(f"✅ Пользователь {target_id} успешно добавлен как {role}!")

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Возврат в главное меню... 🛠️",
        reply_markup=get_main_menu(admin_id, ADMIN_ID, "owner")
    )
    return ConversationHandler.END

async def cancel_admin_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fallback: If user clicks 'Cancel' or types /cancel."""
    user_id = update.effective_user.id
    await update.message.reply_text(
        "Действие отменено.",
        reply_markup=get_main_menu(user_id, ADMIN_ID, "owner")
    )
    return ConversationHandler.END

# --- THE CONVERSATION HANDLER DEFINITION ---
admin_conv = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^➕ Добавить сотрудника$"), start_add_user_flow)],
    states={
        ADDING_USER_FLOW: [
            MessageHandler(filters.StatusUpdate.USERS_SHARED, process_user_shared),
            CallbackQueryHandler(handel_role_callback, pattern="^setrole_"),
            MessageHandler(filters.Regex("^🔙 Отмена$"), cancel_admin_flow)
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_admin_flow)],
)