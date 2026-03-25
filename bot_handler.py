import os
import sqlite3
import logging
import time
from telegram import Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

# Importing tools from your services file
from core.services import generate_marketing_post, init_all_dbs, create_facebook_deep_link

load_dotenv()

# Log configuration for YOUR computer (English)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Security: Only the mechanic's chat ID can trigger the AI
AUTHORIZED_USER_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles button clicks. 
    Interface: Russian | Logs: English
    """
    query = update.callback_query
    # Russian "toast" notification
    await query.answer(text="Обработка...") 
    data = query.data 
    
    if data.startswith("accept_"):
        post_id = data.split("_")[1]
        try:
            with sqlite3.connect("manul_leads.db") as conn:
                conn.execute("UPDATE leads SET status = ? WHERE post_url LIKE ?", ("confirmed", f"%{post_id}%"))
            
            # Russian status update in Telegram
            new_text = f"{query.message.text}\n\n✅ **Статус: Подтверждено וсохранено!**"
            await query.edit_message_text(text=new_text, parse_mode='MarkdownV2')
            
            # English log for your terminal
            logging.info(f"Lead {post_id} confirmed in database.")
            
        except Exception as e:
            logging.error(f"Database error: {e}")
            await query.edit_message_text(text=f"{query.message.text}\n\n⚠️ **Ошибка базы данных**")

    elif data == "edit_post":
        await query.message.replay_text("✍️ Напишите, что именно вы хотите изменить в тексте (на русском), и я переделаю пост.")
        # "ConversationHandler" in the next time write here
    
    elif data == "ignore":
        # Russian ignore status
        await query.edit_message_text(text=f"{query.message.text}\n\n❌ **Статус: Проигнорировано.**", parse_mode='MarkdownV2')
        logging.info("Lead was ignored by the user.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles images for Facebook marketing.
    Interface: Russian | Output: Hebrew | Logs: English
    """
    # Security Check
    if update.message.from_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("⛔ Доступ запрещен.")
        return
    
    # Create special file for upload
    timestamp = int(time.time())
    file_name = f"marketing_{update.message.from_user.id}_{timestamp}.jpg"
    image_path = os.path.join("uploads", file_name)

    try:
        # Download image
        photo_file = await update.message.photo[-1].get_file()
        await photo_file.download_to_drive(image_path)
        
        # Russian progress message for the mechanic
        await update.message.reply_text("🛠️ Генерирую рекламный пост на иврите... Пожалуйста, подождите.")
        
        # This function (in services.py) generates HEBREW text
        marketing_content = generate_marketing_post(image_path)

        # Create facebook deep link
        fb_url = create_facebook_deep_link(marketing_content)
        
        # Save to database (Status and logging in English)
        with sqlite3.connect("manul_leads.db") as conn:
            conn.execute("INSERT INTO marketing_posts (image_path, generated_content) VALUES (?, ?)", 
                         (image_path, marketing_content))

        # Create key board
        keyboard = [
            [InlineKeyboardButton("🚀 Опубликовать (Facebook)", url=fb_url)],
            [InlineKeyboardButton("✍️ Редактировать", callback_data="edit_post")],
            [InlineKeyboardButton("❌ Отменить", callback_data="ignore")]
        ]
        
        # Sending the Hebrew post to the mechanic so he can copy it to Facebook
        await update.message.reply_text(
            f"✨ **Предложение для поста (Иврит):**\n\n{marketing_content}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        logging.info("Marketing post in Hebrew generated successfully.")
        
    except Exception as e:
        logging.error(f"Error handling marketing photo: {e}")
        await update.message.reply_text("❌ Произошла ошибка при создании поста.")

if __name__ == "__main__":
    init_all_dbs() # Ensure DB structure is ready
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        logging.critical("TELEGRAM_BOT_TOKEN missing!")
        exit(1)

    app = ApplicationBuilder().token(token).build()
    
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Terminal message for YOU (English)
    print("🤖 Bot Handler is active. Listening for Marketing Photos and Lead interactions...")
    app.run_polling()