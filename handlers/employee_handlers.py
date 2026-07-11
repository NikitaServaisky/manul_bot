# handlers/employee_handlers.py
import os
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ConversationHandler, MessageHandler, CallbackQueryHandler, CommandHandler, filters, ContextTypes

from keyboards.inline_keyboards import get_employee_area_keyboard
from services.employee_service import fetch_employee_schedule, create_vacation_request, log_user_document, save_shift_submission

# Define states for the Conversation
(
    WAITING_VACATION_START,
    WAITING_VACATION_END,
    WAITING_SICK_LEAVE_DOC,
    WAITING_GENERAL_DOC,
    WAITING_SHIFTS_INPUT,
) = range(5)


async def open_personal_cabinet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point from reply keyboard."""
    # Clear any leftover data in context
    context.user_data.clear()
    
    await update.message.reply_text(
        "👋 Добро пожаловать в ваш личный кабинет.\nВыбери действие из меню ниже:",
        reply_markup=get_employee_area_keyboard()
    )
    return ConversationHandler.END


async def handle_schedule_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetches and displays the schedule."""
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


# ==================== VACATION FLOW ====================

async def start_vacation_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📅 Введите дату начала отпуска в формате YYYY-MM-DD:\n(Или нажмите /cancel для отмены)")
    return WAITING_VACATION_START


async def process_vacation_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        start_date = datetime.strptime(update.message.text, "%Y-%m-%d").date()
        context.user_data["vacation_start"] = start_date
        await update.message.reply_text("📅 Отлично. Теперь введите дату окончания отпуска (YYYY-MM-DD):")
        return WAITING_VACATION_END
    except ValueError:
        await update.message.reply_text("❌ Неверный формат. Пожалуйста, используйте YYYY-MM-DD (Например: 2026-07-15):")
        return WAITING_VACATION_START


async def process_vacation_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        end_date = datetime.strptime(update.message.text, "%Y-%m-%d").date()
        start_date = context.user_data.get("vacation_start")
        
        if end_date < start_date:
            await update.message.reply_text("❌ Дата окончания не может быть раньше даты начала! Попробуйте еще раз:")
            return WAITING_VACATION_END
            
        total_days = (end_date - start_date).days + 1
        user_id = update.effective_user.id
        
        # Save to database
        create_vacation_request(user_id, "vacation", start_date, end_date, float(total_days))
        
        await update.message.reply_text(f"✅ Запрос на отпуск успешно отправлен!\n📅 Период: {start_date} - {end_date} ({total_days} дней).\nОжидайте одобрения владельца.")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Неверный формат. Пожалуйста, используйте YYYY-MM-DD:")
        return WAITING_VACATION_END


# ==================== DOCUMENT UPLOAD FLOW ====================

async def start_sick_leave_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🤒 Пожалуйста, отправьте фото или файл справки о больничном (Document):\n(Или нажмите /cancel)")
    context.user_data["doc_type"] = "sick_leave"
    return WAITING_SICK_LEAVE_DOC


async def start_general_doc_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📁 Пожалуйста, отправьте ваш Топливный/Форма 101 или другой документ как файл:")
    context.user_data["doc_type"] = "id_copy"
    return WAITING_GENERAL_DOC


async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generic file downloader and database logger for employee attachments."""
    user_id = update.effective_user.id
    doc_type = context.user_data.get("doc_type", "contract")    
    # Check if sent as document or photo
    document = update.message.document
    photo = update.message.photo[-1] if update.message.photo else None
    
    if not document and not photo:
        await update.message.reply_text("❌ Пожалуйста, отправьте файл или фотографию документа.")
        return
        
    # Get Telegram file ID
    file_id = document.file_id if document else photo.file_id
    file_name = document.file_name if document else f"photo_{int(datetime.now().timestamp())}.jpg"
    file_size = int((document.file_size if document else photo.file_size) / 1024)
    
    tg_file = await context.bot.get_file(file_id)
    
    # Store inside your existing repository structure
    local_dir = f"./uploads/employees/{user_id}"
    os.makedirs(local_dir, exist_ok=True)
    file_path = os.path.join(local_dir, file_name)
    
    await tg_file.download_to_drive(file_path)
    
    # DB Save
    log_user_document(user_id, doc_type, file_path, file_name, file_size)
    
    await update.message.reply_text("✅ Документ успешно загружен и отправлен на проверку администратору!")
    return ConversationHandler.END


# ==================== SUBMIT SHIFTS FLOW ====================

async def start_shifts_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "✍️ Напишите ваши пожелания по сменам на следующую неделю.\n"
        "Например: 'Понедельник и Среда - только утро, Четверг - выходной':"
    )
    return WAITING_SHIFTS_INPUT


async def process_shifts_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_notes = update.message.text
    
    # For MVP, we save the note targeted at next Sunday's schedule initiation
    next_week_date = datetime.now().date() + timedelta(days=(6 - datetime.now().weekday() + 1) % 7)
    
    save_shift_submission(user_id, next_week_date, "custom", user_notes)
    
    await update.message.reply_text("✅ Ваши пожелания по сменам сохранены и переданы руководству!")
    return ConversationHandler.END


async def cancel_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Действие отменено.")
    return ConversationHandler.END

async def handle_invalid_document_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles cases where the user sends text instead of a file/photo during document upload."""
    await update.message.reply_text(
        "❌ Это не файл и не фотография.\n"
        "Пожалуйста, отправьте документ как файл (Document) или сделайте фото справки.\n"
        "Если вы хотите отменить действие, нажмите /cancel"
    )

# ==================== REGISTRATION ROUTER ====================

# This Conversation Handler replaces the basic employee_conv from last step
employee_conv = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Text("💼 Личный кабинет"), open_personal_cabinet),
        CallbackQueryHandler(start_vacation_request, pattern="^emp_vacation$"),
        CallbackQueryHandler(start_sick_leave_upload, pattern="^emp_sick$"),
        CallbackQueryHandler(start_general_doc_upload, pattern="^emp_upload_doc$"),
        CallbackQueryHandler(start_shifts_submission, pattern="^emp_submit_shifts$"),
    ],
    states={
        WAITING_VACATION_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_vacation_start)],
        WAITING_VACATION_END: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_vacation_end)],
        
        WAITING_SICK_LEAVE_DOC: [
            MessageHandler(filters.Document.ALL | filters.PHOTO, handle_file_upload),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_invalid_document_input) # <- תופס טקסט שגוי
        ],
        
        WAITING_GENERAL_DOC: [
            MessageHandler(filters.Document.ALL | filters.PHOTO, handle_file_upload),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_invalid_document_input) # <- תופס טקסט שגוי
        ],
        
        WAITING_SHIFTS_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_shifts_input)],
    },
    fallbacks=[CommandHandler("cancel", cancel_action)],
    per_message=False # Clears the warning from python-telegram-bot
)

schedule_handler = CallbackQueryHandler(handle_schedule_view, pattern="^emp_schedule$")