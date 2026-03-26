import os
import sqlite3
import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler
)
from dotenv import load_dotenv

# Import modular logic from services
from core.services import (
    init_all_dbs, 
    is_user_authorized, 
    generate_marketing_post, 
    create_facebook_deep_link
)

load_dotenv()

# Logger Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# State for ConversationHandler
EDITING_TEXT = 1

def get_marketing_keyboard(fb_url):
    """Generates the inline keyboard for marketing actions."""
    keyboard = [
        [InlineKeyboardButton("🚀 Опубликовать (Facebook)", url=fb_url)],
        [InlineKeyboardButton("✍️ Редактировать", callback_data="edit_post")],
        [InlineKeyboardButton("❌ Отменить", callback_data="ignore_marketing")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- CONVERSATION FUNCTIONS FOR EDITING ---

async def start_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the edit conversation when 'Edit' is clicked."""
    query = update.callback_query
    await query.answer()
    
    # Check if we have an image to edit
    if 'last_image_path' not in context.user_data:
        await query.message.reply_text("❌ Context lost. Please upload a new photo.")
        return ConversationHandler.END
        
    await query.message.reply_text("✍️ Напишите, что изменить (на русском). Например: 'Сделай короче' или 'Добавь скидку 10%'.")
    return EDITING_TEXT

async def process_edit_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes the text input and calls Gemini again."""
    user_id = update.message.from_user.id
    user_instruction = update.message.text
    image_path = context.user_data.get('last_image_path')

    status_msg = await update.message.reply_text("🔄 Переделываю пост...")

    try:
        # Calls the updated service function
        new_content = generate_marketing_post(image_path, instruction=user_instruction)
        fb_url = create_facebook_deep_link(new_content)
        
        await update.message.reply_text(
            f"✨ **Обновленный вариант:**\n\n{new_content}",
            reply_markup=get_marketing_keyboard(fb_url)
        )
        await status_msg.delete()
    except Exception as e:
        logging.error(f"Edit Error: {e}")
        await update.message.reply_text("❌ Ошибка при обновлении.")

    return ConversationHandler.END

async def cancel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the edit flow."""
    await update.message.reply_text("Отменеנו.")
    return ConversationHandler.END

# --- NORMAL HANDLERS ---

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles simple button interactions (Accept/Ignore)."""
    query = update.callback_query
    await query.answer() 
    data = query.data 
    
    if data.startswith("accept_"):
        post_id = data.split("_")[1]
        user_id = query.from_user.id
        try:
            with sqlite3.connect("manul_leads.db") as conn:
                conn.execute(
                    "UPDATE leads SET status = ?, assigned_to = ? WHERE post_url LIKE ?", 
                    ("confirmed", user_id, f"%{post_id}%")
                )
            await query.edit_message_text(text=f"{query.message.text}\n\n✅ Статус: Подтверждено")
        except Exception as e:
            logging.error(f"Callback DB Error: {e}")

    elif data in ["ignore", "ignore_marketing"]:
        await query.edit_message_text(text=f"{query.message.text}\n\n❌ Статус: Проигнорировано")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes incoming photos for marketing content."""
    user_id = update.message.from_user.id
    
    if not is_user_authorized(user_id):
        await update.message.reply_text("⛔ Доступ запрещен.")
        return
    
    timestamp = int(time.time())
    file_name = f"marketing_{user_id}_{timestamp}.jpg"
    image_path = os.path.join("uploads", file_name)

    try:
        photo_file = await update.message.photo[-1].get_file()
        await photo_file.download_to_drive(image_path)
        
        # CRITICAL: Save the path for editing later
        context.user_data['last_image_path'] = image_path
        
        status_msg = await update.message.reply_text("🛠️ Генерирую пост...")
        marketing_content = generate_marketing_post(image_path)
        
        with sqlite3.connect("manul_leads.db") as conn:
            conn.execute(
                "INSERT INTO marketing_posts (image_path, generated_content, user_id) VALUES (?, ?, ?)", 
                (image_path, marketing_content, user_id)
            )

        fb_url = create_facebook_deep_link(marketing_content)
        await update.message.reply_text(
            f"✨ **Предложение:**\n\n{marketing_content}",
            reply_markup=get_marketing_keyboard(fb_url)
        )
        await status_msg.delete()
    except Exception as e:
        logging.error(f"Photo Error: {e}")
        await update.message.reply_text("❌ Ошибка.")

if __name__ == "__main__":
    init_all_dbs()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    app = ApplicationBuilder().token(token).build()

    # 1. Setup Conversation for Editing (Must be added BEFORE other callback handlers)
    edit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_edit, pattern="^edit_post$")],
        states={
            EDITING_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_edit_request)],
        },
        fallbacks=[CallbackQueryHandler(cancel_edit, pattern="^ignore_marketing$")],
    )

    app.add_handler(edit_conv)
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("🤖 Bot is live. I can go to sleep!")
    app.run_polling()