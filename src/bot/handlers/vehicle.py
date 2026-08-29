import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from src.bot.keyboards.reply import get_main_menu, get_user_selector_keyboard
from src.bot.keyboards.inline import get_skip_keyboard
from src.services.customer_service import register_customer_and_vehicle
from src.core.auth_service import is_user_authorized

logger = logging.getLogger(__name__)

# States for the Vehicle & Customer registration conversation
(
    WAITING_FOR_PLATE, WAITING_FOR_CUST_NAME, WAITING_FOR_CUST_PHONE,
    WAITING_FOR_BRAND, WAITING_FOR_MODEL, WAITING_FOR_ENGINE_CODE
) = range(20, 26) # Starting from 20 to avoid state collision with admin flows


async def start_add_vehicle_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: Authorized user triggers vehicle flow."""
    user_id = update.effective_user.id
    
    # Secure check: Only active garage staff can add vehicles
    if not is_user_authorized(user_id):
        await update.message.reply_text("❌ Нет доступа.")
        return ConversationHandler.END

    # We open the layout keyboard with the cancel button
    await update.message.reply_text(
        "🚗 Введите НОМЕР АВТОМОБИЛЯ (Гос. номер):",
        reply_markup=get_user_selector_keyboard() # Using keyboard with 🔙 Отмена
    )
    return WAITING_FOR_PLATE


async def process_vehicle_plate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: Plate received, ask for Customer Name."""
    user_text = update.message.text.strip().upper()

    if user_text == "🔙 ОТМЕНА":
        return await cancel_vehicle_flow(update, context)

    context.user_data["pending_plate"] = user_text
    await update.message.reply_text("📝 Введите ИМЯ и ФАМИЛИЮ владельца (Клиента):")
    return WAITING_FOR_CUST_NAME


async def process_customer_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 3: Name received, ask for Phone."""
    context.user_data["pending_cust_name"] = update.message.text.strip()
    await update.message.reply_text("📞 Введите НОМЕР ТЕЛЕФОНА клиента:")
    return WAITING_FOR_CUST_PHONE


async def process_customer_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 4: Phone received, ask for Vehicle Brand."""
    context.user_data["pending_cust_phone"] = update.message.text.strip()
    await update.message.reply_text("🏎 Введите МАРКУ автомобиля (Например: Audi, VW):")
    return WAITING_FOR_BRAND


async def process_vehicle_brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 5: Brand received, ask for Model."""
    context.user_data["pending_brand"] = update.message.text.strip()
    await update.message.reply_text("🚘 Введите МОДЕЛЬ автомобиля (Например: Golf, Leon):")
    return WAITING_FOR_MODEL


async def process_vehicle_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 6: Model received, ask for Engine Code (Optional)."""
    context.user_data["pending_model"] = update.message.text.strip()
    
    # Provide an inline skip button for the engine code step
    await update.message.reply_text(
        "🛠 Введите КОД ДВИГАТЕЛЯ (или нажмите Пропустить):",
        reply_markup=get_skip_keyboard("engine")
    )
    return WAITING_FOR_ENGINE_CODE


async def process_engine_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Final Step: Process text input or skip callback, then save to DB."""
    query = update.callback_query
    extracted_value = None

    if query:
        await query.answer()
        await query.edit_message_text("⚙️ Код двигателя: Пропущено")
        msg = query.message
        extracted_value = "" 
    else:
        user_text = update.message.text.strip()
        if user_text == "🔙 Отмена":
            return await cancel_vehicle_flow(update, context)
        extracted_value = user_text
        msg = update.message

    # Pulling everything out of context memory
    plate = context.user_data.get("pending_plate")
    cust_name = context.user_data.get("pending_cust_name")
    phone = context.user_data.get("pending_cust_phone")
    brand = context.user_data.get("pending_brand")
    model = context.user_data.get("pending_model")

    if not all([plate, cust_name, phone, brand, model]):
        await msg.reply_text("❌ Ошибка: Некоторые обязательные данные были утеряны. Попробуйте снова.")
        context.user_data.clear()
        return ConversationHandler.END

    # Call secure Service Layer to process encryption and database insertion
    success = register_customer_and_vehicle(
        full_name=cust_name,
        phone_number=phone,
        license_plate=plate,
        brand=brand,
        model=model,
        engine_code=extracted_value
    )

    if success:
        await msg.reply_text(f"✅ Автомобиль {brand} {model} [{plate}] и клиент {cust_name} успешно сохранены!")
    else:
        await msg.reply_text("❌ Произошла ошибка при сохранении данных в базу. Проверьте логи.")

    # Redirect securely back to main menu
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Возврат в меню... 🛠️",
        reply_markup=get_main_menu(update.effective_user.id)
    )
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_vehicle_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the vehicle flow and flushes context."""
    context.user_data.clear()
    await update.message.reply_text("❌ Добавление автомобиля отменено.")
    return ConversationHandler.END


# Defining the modular ConversationHandler to export directly into main.py
vehicle_conv = ConversationHandler(
    entry_points=[MessageHandler(filters.Text("➕ Добавить автомобиль"), start_add_vehicle_flow)],
    states={
        WAITING_FOR_PLATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_vehicle_plate)],
        WAITING_FOR_CUST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_customer_name)],
        WAITING_FOR_CUST_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_customer_phone)],
        WAITING_FOR_BRAND: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_vehicle_brand)],
        WAITING_FOR_MODEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_vehicle_model)],
        WAITING_FOR_ENGINE_CODE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_engine_code),
            CallbackQueryHandler(process_engine_code, pattern="^skip_engine$")
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_vehicle_flow)],
)