from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from services.employee_service import update_vacation_status

def get_manager_area_keyboard():
    """Generate the inline keyboard for the manager panel."""
    # FIXED: Corrected assignment operator, parameter name (callback_data), and string values
    keyboard = [
        [InlineKeyboardButton("📋 Заявки на отпуск (Vacations)", callback_data="mgr_pending_vacations")],
        [InlineKeyboardButton("📁 Новые документы (Documents)", callback_data="mgr_new_docs")],
        [InlineKeyboardButton("📊 Пожелания по сменам (Shifts)", callback_data="mgr_view_shifts")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def open_manager_cabinet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the manager dashboard."""
    # Since this can be called via router, we support both message and callback query
    target = update.message if update.message else update.callback_query.message
    await target.reply_text(
        "⚡ **Панель управления Manul Garage**\n"
        "Добро пожаловать в кабинет администратора. Выберите раздел для управления:",
        reply_markup=get_manager_area_keyboard(),
        parse_mode="Markdown"
    )

# Placeholders for manager actions to expand later
async def handle_mgr_vacations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("📋 Здесь будет список заявок на отпуск, ожидающих одобрения.") 

async def handle_mgr_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("📁 Здесь будут загруженные файлы сотрудников для проверки.")

async def handle_mgr_shifts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("📊 Здесь будет выписка по пожеланиям смен на следующую неделю.")

async def handle_manager_vacation_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data 
    request_id = int(data.split("_")[-1])
    
    if "approve" in data:
        status = "Approved"
        manager_reply = "✅ Вы одобрили отпуск. Статус обновлен в базе данных (Approved)."
        employee_emoji = "🎉"
        status_russian = "ОДОБРЕН"
    else:
        status = "Rejected"
        manager_reply = "❌ Вы отклонили запрос. Статус обновлен в базе данных (Rejected)."
        employee_emoji = "❌"
        status_russian = "ОТКЛОНЕН"
        
    db_info = update_vacation_status(request_id, status)
    
    await query.message.edit_text(manager_reply)
    
    if db_info:
        employee_id, start_date, end_date = db_info
        # עדכון לעובד ברוסית
        employee_msg = (
            f"{employee_emoji} **Обновление по вашему запросу на отпуск:**\n"
            f"Ваш запрос на отпуск с {start_date} по {end_date} был **{status_russian}** менеджером."
        )
        try:
            await context.bot.send_message(chat_id=employee_id, text=employee_msg, parse_mode="Markdown")
        except Exception as e:
            print(f"Failed to notify employee {employee_id}: {e}")

# Manager Handlers registration list
manager_handlers = [
    CallbackQueryHandler(handle_mgr_vacations, pattern="^mgr_pending_vacations$"),
    CallbackQueryHandler(handle_mgr_docs, pattern="^mgr_new_docs$"),
    CallbackQueryHandler(handle_mgr_shifts, pattern="^mgr_view_shifts$"),
    CallbackQueryHandler(handle_manager_vacation_decision, pattern="^vact_mgr_(approve|reject)_"),
]