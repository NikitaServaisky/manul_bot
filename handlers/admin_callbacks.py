import os
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from keyboards.reply_keyboards import get_main_menu, get_user_selector_keyboard
from keyboards.inline_keyboards import get_role_selection_keyboard, get_salary_type_keyboard
from core.auth_service import add_user

logger = logging.getLogger(__name__)
ADMIN_ID = int(os.getenv("TELEGRAM_CHAT_ID", 0))

# Import/define states locally for redirection mapping
(
    ADDING_USER_FLOW, WAITING_FOR_NAME, WAITING_FOR_ID, WAITING_FOR_PHONE,
    WAITING_FOR_BANK_NAME, WAITING_FOR_BANK_BRANCH, WAITING_FOR_BANK_ACCOUNT,
    WAITING_FOR_SALARY_TYPE, WAITING_FOR_RATE, WAITING_FOR_ROLE
) = range(1, 11)


async def start_add_user_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: Admin selects employee from contacts."""
    await update.message.reply_text(
        "Нажмите кнопку ниже, чтобы выбрать сотрудника:",
        reply_markup=get_user_selector_keyboard(),
    )
    return ADDING_USER_FLOW


async def process_user_shared(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: ID extracted, ask for Name."""
    shared_data = update.message.users_shared or update.message.user_shared
    target_id = None

    if shared_data:
        if hasattr(shared_data, "users") and shared_data.users:
            target_id = shared_data.users[0].user_id
        elif hasattr(shared_data, "user_id"):
            target_id = shared_data.user_id

    if not target_id:
        await update.message.reply_text("❌ Ошибка получения ID.")
        return ADDING_USER_FLOW

    context.user_data["pending_id"] = target_id
    await update.message.reply_text("📝 Введите ИМЯ и ФАМИЛИЮ сотрудника:")
    return WAITING_FOR_NAME


async def process_user_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 3: Name received, ask for ID Number."""
    context.user_data["pending_name"] = update.message.text
    await update.message.reply_text("🪪 Введите НОМЕР УДОСТОВЕРЕНИЯ (ID):")
    return WAITING_FOR_ID


async def process_user_id_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 4: ID Number received, ask for Phone."""
    context.user_data["pending_id_num"] = update.message.text
    await update.message.reply_text("📞 Введите НОМЕР ТЕЛЕФОНА:")
    return WAITING_FOR_PHONE


async def process_user_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 5: Phone received, ask for Bank Name (New Step)."""
    context.user_data["pending_phone"] = update.message.text
    await update.message.reply_text("🏦 Введите НАЗВАНИЕ БАНКА (например: Leumi, Hapoalim):")
    return WAITING_FOR_BANK_NAME


async def process_bank_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 6: Bank Name received, ask for Branch Number (New Step)."""
    context.user_data["pending_bank_name"] = update.message.text
    await update.message.reply_text("🏢 Введите НОМЕР ФИЛИАЛА (Branch):")
    return WAITING_FOR_BANK_BRANCH


async def process_bank_branch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 7: Branch Number received, ask for Account Number (New Step)."""
    context.user_data["pending_bank_branch"] = update.message.text
    await update.message.reply_text("💳 Введите НОМЕР СЧЕТА (Account Number):")
    return WAITING_FOR_BANK_ACCOUNT


async def process_bank_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 8: Account Number received, ask for Salary Type."""
    context.user_data["pending_bank_account"] = update.message.text
    await update.message.reply_text(
        "💰 Выберите ТИП ОПЛАТЫ:",
        reply_markup=get_salary_type_keyboard()
    )
    return WAITING_FOR_SALARY_TYPE


async def process_salary_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 9: Salary type selected via Inline, ask for Rate."""
    query = update.callback_query
    await query.answer()
    
    salary_type = query.data.split("_")[1]
    context.user_data["pending_salary_type"] = salary_type
    
    await query.edit_message_text(f"💵 Введите СТАВКУ для типа '{salary_type}':")
    return WAITING_FOR_RATE


async def process_salary_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 10: Rate received, ask for Role."""
    try:
        context.user_data["pending_rate"] = float(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Введите число (например: 50.5):")
        return WAITING_FOR_RATE

    target_id = context.user_data.get("pending_id")
    await update.message.reply_text(
        "🛠 Какую РОЛЬ назначить?",
        reply_markup=get_role_selection_keyboard(target_id),
    )
    return WAITING_FOR_ROLE


async def handel_role_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Final Step: Save everything to DB via the secure service layer."""
    query = update.callback_query
    admin_id = update.effective_user.id
    await query.answer()

    data = query.data.split("_")
    if data[0] != "setrole": return

    target_id = int(data[1])
    role = data[2]
    saved_username = context.user_data.get("pending_name")
    
    # Construct the final payload dictionary including bank credentials
    user_data = {
        "user_id": target_id,
        "username": saved_username,
        "role": role,
        "id_number": context.user_data.get("pending_id_num"),
        "phone_number": context.user_data.get("pending_phone"),
        "bank_name": context.user_data.get("pending_bank_name"),
        "bank_branch": context.user_data.get("pending_bank_branch"),
        "bank_account_num": context.user_data.get("pending_bank_account"),
        "salary_type": context.user_data.get("pending_salary_type"),
        "base_salary_rate": context.user_data.get("pending_rate")
    }

    try:
        add_user(**user_data)
        await query.edit_message_text(f"✅ Сотрудник {user_data['username']} успешно добавлен!")
    except Exception as e:
        logger.exception(f"❌ DB ERROR: {e}")
        await query.edit_message_text("❌ Ошибка при сохранении в базу данных.")

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Возврат в меню... 🛠️",
        reply_markup=get_main_menu(admin_id, ADMIN_ID, "owner"),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_admin_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the current conversation flow and cleans user_data context."""
    context.user_data.clear()
    await update.message.reply_text("❌ Действие отменено.")
    return ConversationHandler.END