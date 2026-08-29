import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from src.bot.keyboards.reply import get_main_menu, get_user_selector_keyboard
from src.bot.keyboards.inline import get_role_selection_keyboard, get_salary_type_keyboard, get_skip_keyboard
from src.core.auth_service import add_user, is_user_admin

logger = logging.getLogger(__name__)


# Import/define states locally for redirection mapping
(
    ADDING_USER_FLOW, WAITING_FOR_NAME, WAITING_FOR_ID, WAITING_FOR_PHONE,
    WAITING_FOR_BANK_NAME, WAITING_FOR_BANK_BRANCH, WAITING_FOR_BANK_ACCOUNT,
    WAITING_FOR_SALARY_TYPE, WAITING_FOR_RATE, WAITING_FOR_ROLE
) = range(1, 11)


async def _handle_optional_input(update: Update, context: ContextTypes.DEFAULT_TYPE, field_name: str):
    """
    Helper to handle optional fields safely. 
    Handles both normal text inputs and skip callback queries without breaking.
    """
    query = update.callback_query

    if query:
        await query.answer()
        extracted_value = None
        msg = query.message
    else:
        extracted_value = update.message.text if update.message.text else None
        msg = update.message

    # If the user typed text save it, if pushed skip, keep whitout changes or save None
    if extracted_value is not None:
        context.user_data[f'pending_{field_name}'] = extracted_value
    elif f'pending_{field_name}' not in context.user_data:
        context.user_data[f'pending_{field_name}'] = None

    return msg


async def start_add_user_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: Admin selects employee from contacts."""
    user_id = update.message.from_user.id
    # The service layer now securely evaluates both .env and DB permissions
    if not is_user_admin(user_id):
        await update.message.reply_text("❌ Извините, у вас нет прав для выполнения этого действия.")
        return ConversationHandler.END

    await update.message.reply_text(
        "Нажмите кнопку ниже, чтобы выбрать сотрудника:",
        reply_markup=get_user_selector_keyboard(),
    )
    return ADDING_USER_FLOW


async def process_user_shared(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: Extract ID (and optionally phone/name if sent via Contact), then ask for Name."""
    
    # 1. Native Telegram Contact sharing
    if update.message.contact:
        contact = update.message.contact
        context.user_data["pending_id"] = contact.user_id
        
        # Pre-fill phone into state if available
        if contact.phone_number:
            context.user_data["pending_phone"] = contact.phone_number
            
        # Extract full name safely
        full_name = f'{contact.first_name or ""} {contact.last_name or ""}'.strip()
        if full_name:
            context.user_data["pending_name"] = full_name
            await update.message.reply_text(
                f"👤 Извлечено имя: {full_name}\n"
                f"📞 Извлечён номер: {contact.phone_number or 'Не указан'}\n\n"
                f"📝 Подтвердите или введите ИМЯ и ФАМИЛИЮ заново:"
            )
            return WAITING_FOR_NAME

    # 2. UsersShared request button
    shared_data = update.message.users_shared or update.message.user_shared
    if shared_data:
        if hasattr(shared_data, "users") and shared_data.users:
            context.user_data["pending_id"] = shared_data.users[0].user_id
        elif hasattr(shared_data, "user_id"):
            context.user_data["pending_id"] = shared_data.user_id

    if not context.user_data.get("pending_id"):
        await update.message.reply_text("❌ Ошибка получения ID.")
        return ADDING_USER_FLOW

    await update.message.reply_text("📝 Введите ИМЯ и ФАМИЛИЮ сотрудника:")
    return WAITING_FOR_NAME


async def process_user_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 3: Name received, ask for ID Number."""
    context.user_data["pending_name"] = update.message.text.strip()
    await update.message.reply_text("🪪 Введите НОМЕР УДОСТОВЕРЕНИЯ (ID):")
    return WAITING_FOR_ID


async def process_user_id_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 4: ID Number received (Required), ask for Phone (or skip to Bank if already collected)."""
    context.user_data["pending_id_num"] = update.message.text.strip()
    
    # If phone was already extracted during step 2 (Contact sharing), jump straight to Bank Name
    if context.user_data.get("pending_phone"):
        phone = context.user_data["pending_phone"]
        await update.message.reply_text(
            f"📞 Номер телефона уже сохранен ({phone}).\n"
            f"🏦 Введите НАЗВАНИЕ БАНКА (или нажмите Пропустить):",
            reply_markup=get_skip_keyboard("bank")
        )
        return WAITING_FOR_BANK_NAME

    # Otherwise request phone input with skip option
    await update.message.reply_text(
        "📞 Введите НОМЕР ТЕЛЕФОНА (или нажмите Пропустить):",
        reply_markup=get_skip_keyboard("phone")    
    )
    return WAITING_FOR_PHONE


async def process_user_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 5: Handle Phone input (text or skip) and ask for Bank Name (Optional)."""
    msg = await _handle_optional_input(update, context, "phone")
    
    await msg.reply_text(
        "🏦 Введите НАЗВАНИЕ БАНКА (или нажмите Пропустить):",
        reply_markup=get_skip_keyboard("bank")
    )
    return WAITING_FOR_BANK_NAME


async def process_bank_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 6: Handle Bank Name input (text or skip) and ask for Branch Number (Optional)."""
    msg = await _handle_optional_input(update, context, "bank_name")
    
    await msg.reply_text(
        "🏢 Введите НОМЕР ФИЛИАЛА (Branch) (или нажмите Пропустить):",
        reply_markup=get_skip_keyboard("branch")
    )
    return WAITING_FOR_BANK_BRANCH


async def process_bank_branch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 7: Handle Branch input (text or skip) and ask for Account Number (Optional)."""
    msg = await _handle_optional_input(update, context, "bank_branch")
    
    await msg.reply_text(
        "💳 Введите НОМЕР СЧЕТА (Account Number) (или нажмите Пропустить):",
        reply_markup=get_skip_keyboard("account")
    )
    return WAITING_FOR_BANK_ACCOUNT


async def process_bank_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 8: Handle Account input (text or skip) and ask for Salary Type (Required)."""
    msg = await _handle_optional_input(update, context, "bank_account")
    
    await msg.reply_text(
        "💰 Выберите ТИП ОПЛАТЫ:",
        reply_markup=get_salary_type_keyboard()
    )
    return WAITING_FOR_SALARY_TYPE


async def process_salary_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 9: Salary type selected via Inline, ask for Rate clearly and open the reply keyboard."""
    query = update.callback_query
    await query.answer()
    
    salary_type = query.data.split("_")[1]
    context.user_data["pending_salary_type"] = salary_type
    
    # Edit the inline message to remove buttons so the user cannot click them again
    await query.edit_message_text(f"📋 Выбран тип оплаты: {salary_type}")
    
    # Send a fresh message and explicitly open the layout keyboard with the cancel button
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"💵 Введите СТАВКУ (сумму денег) для типа '{salary_type}':\n(Например: 150 или 50.5)",
        reply_markup=get_user_selector_keyboard()
    )
    return WAITING_FOR_RATE


async def process_salary_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 10: Rate received, check for cancel button text, ask for Role."""
    user_text = update.message.text.strip()

    # Intercept if the user clicks the persistent layout cancel button
    if user_text == "🔙 Отмена":
        return await cancel_admin_flow(update, context)

    try:
        context.user_data["pending_rate"] = float(user_text)
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

    # handle of click cancel
    if query.data == "cancel_admin":
        await query.edit_message_text("❌ Действие отменено.")
        context.user_data.clear()
        return ConversationHandler.END

    data = query.data.split("_")
    if data[0] != "setrole": 
        return

    target_id = int(data[1])
    role = data[2]
    saved_username = context.user_data.get("pending_name")
    
    user_data = {
        "user_id": target_id,
        "username": saved_username,
        "role": role,
        "id_number": context.user_data.get("pending_id_num"),
        "phone_number": context.user_data.get("pending_phone"),
        "bank_name": context.user_data.get("pending_bank_name"),
        "bank_branch": context.user_data.get("pending_bank_branch"),
        "bank_account_number": context.user_data.get("pending_bank_account"),
        "salary_type": context.user_data.get("pending_salary_type"),
        "base_salary_rate": context.user_data.get("pending_rate")
    }

    try:
        # Capture the returned ID from service layer execution
        saved_db_id = add_user(**user_data)
        
        if saved_db_id and saved_db_id > 0:
            await query.edit_message_text(f"✅ Сотрудник {user_data['username']} успешно добавлен!")
        else:
            await query.edit_message_text("❌ Ошибка: Не удалось сохранить пользователя в базу данных (Constraint Violation).")

    except Exception as e:
        logger.exception(f"❌ DB ERROR: {e}")
        await query.edit_message_text("❌ Ошибка при сохранении в базу данных.")

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Возврат в меню... 🛠️",
        reply_markup=get_main_menu(admin_id),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_admin_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the current conversation flow and cleans user_data context."""
    context.user_data.clear()
    await update.message.reply_text("❌ Действие отменено.")
    return ConversationHandler.END