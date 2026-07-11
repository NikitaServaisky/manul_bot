import os
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ConversationHandler, MessageHandler, CallbackQueryHandler, CommandHandler, filters, ContextTypes

from keyboards.inline_keyboards import get_employee_area_keyboard
from services.employee_service import fetch_employee_schedule

async def open_personal_cabinet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggered when the user clicks '💼 Личный кабинет' in the reply menu."""
    await update.message.reply_text(
        "👋 Добро пожаловать в ваш личный кабинет.\nВыбери действие из меню ниже:",
        reply_markup=get_employee_area_keyboard()
    )

async def handle_schedule_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggered by the 'emp_schedule' callback query."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    today = datetime.now().date()
    end_week = today + timedelta(days=7)
    
    shifts = fetch_employee_schedule(user_id, today, end_week)
    
    if not shifts:
        await query.message.reply_text("📅 На эту неделю нет запланированных смен.")
        return
        
    response = "📋 **Ваш график работы на ближайшие 7 дней:**\n\n"
    for shift in shifts:
        response += f"🔹 **{shift[0]}** | {shift[1]} - {shift[2]}\n"
        if len(shift) > 4 and shift[4]:
            response += f" 📝 _Заметка:_ {shift[4]}\n"
            
    await query.message.reply_text(response, parse_mode="Markdown")


UPLOAD_DOC, VACATION_DATE = range(2)

employee_conv = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Text("💼 Личный кабинет"), open_personal_cabinet)
    ],
    states={
        # Future states go here
    },
    fallbacks=[
        CommandHandler("cancel", open_personal_cabinet) 
    ]
)

schedule_handler = CallbackQueryHandler(handle_schedule_view, pattern="^emp_schedule$")