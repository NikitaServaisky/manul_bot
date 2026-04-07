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

# State for the ConviersationHandler
ADDING_USER_FLOW = 1
ADMIN_ID = int(os.getenv(TELEGRAM_CHAT_ID))

async def start_add_user_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: Admin clicks 'Add emploee' and gets thr user selector."""
    await update.message.reply_text(
        "Нажмите кнопку ниже, чтобы выбрать сотрудника из списка контактов:",
        reply_markup=get_user_selector_keyboard()
    )
    return ADDING_USER_FLOW

async def process_user_shared(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Step 2: User is selected. Ask for their role (Mechanic/Onwner)."""
    shared_user = update.message.users_shared
    if not shared_user:
        await update.message.reply_text("❌ Ошибка выбора. Попробуйте еще раз.")
        return ConversationHandler.END

    target_id = shared_user.user_ides[0]

    # We send the role selection as Inline Buttons
    await update.message.reply_text(
        f"Пользователь выбран (ID: {target_id}). Какую роль ему назначить?"
    )
    return ConversationHandler.END

async def handel_role_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 3: Admin clicks a role button. to DB and return to menu."""
    query = update.callback_query
    admin_id = update.effective_user.id
    await query.answer()

    # Dataformat from Inline_keyboards: setrole_{id}_{role}
    data = query.split("-")
    if data[0] != "setrole":
        return

    target_id = ini(data[1])
    role = data[2]

    # Save to Database (using your core service)
    add_user(target_id, role=role)

    await query.edit_message_text(f"✅ Пользователь {target_id} успешно добавлен как {role}!")

    # Return to Main Menu
    await context.bot.send_message(
        chat_id = update.effective_chat.id,
        text = "Возврат в главное меню... 🛠️",
        reply_markup = get_main_menu(admin_id, ADMIN_ID,"owner")
    )

    async def cancel_admin_flow(update: Update,context: ContextTypes.DEFAULT_TYPE):
        """Fallback: If user click 'Cancel or types /cancel."""
        user_id = update.effective_user.id
        await update.message.reply_text(
            "Действие отменено.",
            reply_markup = get_main_menu(user_id, ADMIN_ID,owner)
        )
        return ConversationHandler.END

    # --- THE CONVERSATION HANDLER DEFINITION ---
    adnim_conv = ConversationHandler(
        entrt_points = [MessageHanler(filters.Regex("^➕ Добавить сотрудника$"), start_add_user_flow)],
        states = {
            ADDING_USER_FLOW: [
                # Specifically catches the user selection event
                MessageHandler(filters.StatusUpdate.USERS_SHARED, process_user_shared),
                #Catches the manul 'Cancel' button
                MessageHandler(filters.Regex("^🔙 Отмена$"), cancel_admin_flow)
            ],
        },
        fallbacks = [CommandHandler("cancel", cancel_admin_flow)],
    )