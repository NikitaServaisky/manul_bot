from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

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

# Manager Handlers registration list
manager_handlers = [
    CallbackQueryHandler(handle_mgr_vacations, pattern="^mgr_pending_vacations$"),
    CallbackQueryHandler(handle_mgr_docs, pattern="^mgr_new_docs$"),
    CallbackQueryHandler(handle_mgr_shifts, pattern="^mgr_view_shifts$"),
]