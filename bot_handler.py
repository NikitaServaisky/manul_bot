import os
import sqlite3
import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, MessageHandler, filters
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

def get_marketing_keyboard(fb_url):
    """Generates the inline keyboard for marketing actions."""
    keyboard = [
        [InlineKeyboardButton("🚀 Опубликовать (Facebook)", url=fb_url)],
        [InlineKeyboardButton("✍️ Редактировать", callback_data="edit_post")],
        [InlineKeyboardButton("❌ Отменить", callback_data="ignore_marketing")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all button interactions."""
    query = update.callback_query
    await query.answer(text="Обработка...") 
    data = query.data 
    
    # Lead Confirmation Logic
    if data.startswith("accept_"):
        post_id = data.split("_")[1]
        user_id = query.from_user.id
        try:
            with sqlite3.connect("manul_leads.db") as conn:
                conn.execute(
                    "UPDATE leads SET status = ?, assigned_to = ? WHERE post_url LIKE ?", 
                    ("confirmed", user_id, f"%{post_id}%")
                )
            await query.edit_message_text(text=f"{query.message.text}\n\n✅ Status: Confirmed by Mechanic")
        except Exception as e:
            logging.error(f"Callback DB Error: {e}")

    elif data == "edit_post":
        await query.message.reply_text("✍️ Send the text with changes in Russian, and I will regenerate it.")

    elif data in ["ignore", "ignore_marketing"]:
        await query.edit_message_text(text=f"{query.message.text}\n\n❌ Status: Cancelled")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes incoming photos for marketing content."""
    user_id = update.message.from_user.id
    
    # CRM Auth Check
    if not is_user_authorized(user_id):
        await update.message.reply_text("⛔ Доступ запрещен. Обратитесь к администратору.")
        return
    
    timestamp = int(time.time())
    file_name = f"marketing_{user_id}_{timestamp}.jpg"
    image_path = os.path.join("uploads", file_name)

    try:
        # Step 1: Download image
        photo_file = await update.message.photo[-1].get_file()
        await photo_file.download_to_drive(image_path)
        
        # Step 2: Inform user and process AI
        status_msg = await update.message.reply_text("🛠️ Генерирую пост... Пожалуйста, подождите.")
        marketing_content = generate_marketing_post(image_path)
        
        if not marketing_content:
            raise Exception("AI failed to return content")

        # Step 3: Log to Marketing table for CRM
        with sqlite3.connect("manul_leads.db") as conn:
            conn.execute(
                "INSERT INTO marketing_posts (image_path, generated_content, user_id) VALUES (?, ?, ?)", 
                (image_path, marketing_content, user_id)
            )

        # Step 4: Final Output
        fb_url = create_facebook_deep_link(marketing_content)
        await update.message.reply_text(
            f"✨ **Предложение для поста:**\n\n{marketing_content}",
            reply_markup=get_marketing_keyboard(fb_url)
        )
        await status_msg.delete()
        
    except Exception as e:
        logging.error(f"Handle Photo Error: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обработке фото.")

if __name__ == "__main__":
    init_all_dbs()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        logging.critical("Missing Bot Token!")
        exit(1)

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("🤖 Bot is active. Ready for CRM operations.")
    app.run_polling()