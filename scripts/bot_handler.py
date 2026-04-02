import os
import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
    ConversationHandler
)
from dotenv import load_dotenv

# Modular Services
from core.auth_service import is_user_authorized, add_user, get_user_role
from services.ai_logic import analyze_mechanic_work
from core.utils import create_facebook_deep_link, escape_md
from core.database import get_db

load_dotenv()

# Logger Setup
logging.basicConfig(level=logging.INFO, format='%(message)s')

# States for ConversationHandlers
EDITING_TEXT = 1
ADDING_USER_ROLE = 2
WAITING_FOR_POST_IMAGE = 3

# Admin ID from .env
ADMIN_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

# --- KEYBOARDS ---

def get_main_menu_keyboard(user_id):
    """Main persistent keyboard in Russian."""
    role = get_user_role(user_id)
    buttons = [[KeyboardButton("📷 Создать пост")]]
    
    if user_id == ADMIN_ID or role == 'owner':
        buttons.append([KeyboardButton("➕ Добавить пользователя")])
        
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_marketing_keyboard(fb_url):
    """Inline keyboard for post actions."""
    keyboard = [
        [InlineKeyboardButton("🚀 Publish (Facebook)", url=fb_url)],
        [InlineKeyboardButton("✍️ Edit (Изменить)", callback_data="edit_post")],
        [InlineKeyboardButton("✅ Готово (Finish)", callback_data="finish_post")],
        [InlineKeyboardButton("❌ Ignore (Удалить)", callback_data="ignore_marketing")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- UTILITY HANDLERS ---

async def global_ignore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels and returns to main menu."""
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()
    context.user_data.clear() # Wipe context on cancel
    
    await query.edit_message_text("❌ Процесс отменен.")
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Возвращаюсь в главное меню... 🛠️",
        reply_markup=get_main_menu_keyboard(user_id)
    )
    return ConversationHandler.END

async def finish_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finalizes the post."""
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()
    context.user_data.clear() # Wipe context on finish

    await query.edit_message_text("✅ Пост завершен!")
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Отлично! Вы в главном меню.",
        reply_markup=get_main_menu_keyboard(user_id)
    )
    return ConversationHandler.END

# --- START & AUTH ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        "Добро пожаловать в Manul Garage! 🛠️",
        reply_markup=get_main_menu_keyboard(user_id)
    )

async def start_post_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear() # Ensure clean start
    await update.message.reply_text("📷 Отправьте фото или опишите работу текстом.")
    return WAITING_FOR_POST_IMAGE

# --- POST LOGIC ---

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles new photos and wipes old context."""
    context.user_data.clear() # Kill old Mustang data immediately
    user_id = update.effective_user.id
    
    image_path = f"uploads/m_{user_id}_{int(time.time())}.jpg"
    os.makedirs("uploads", exist_ok=True)

    try:
        photo_file = await update.message.photo[-1].get_file()
        await photo_file.download_to_drive(image_path)
        context.user_data['last_image_path'] = image_path
        
        status_msg = await update.message.reply_text("🛠️ Генерирую пост по фото...")
        content = analyze_mechanic_work(image_path)
        context.user_data['last_content'] = content
        
        fb_url = create_facebook_deep_link(content)
        await update.message.reply_text(
            f"✨ **Предложенный пост:**\n\n{content}",
            reply_markup=get_marketing_keyboard(fb_url)
        )
        await status_msg.delete()
        return EDITING_TEXT
    except Exception as e:
        logging.error(f"Photo error: {e}")
        await update.message.reply_text("❌ Ошибка при обработке.")
        return WAITING_FOR_POST_IMAGE

async def handle_text_only_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles text-only posts and wipes old context."""
    user_text = update.message.text
    if not user_text:
        return WAITING_FOR_POST_IMAGE

    # Clear old data so the AI doesn't remember previous cars/photos
    context.user_data.clear() 
    
    status_msg = await update.message.reply_text("✍️ Готовлю пост на основе текста...")
    
    try:
        content = analyze_mechanic_work(None, instruction=user_text)
        context.user_data['last_content'] = content
        context.user_data['last_image_path'] = None
        
        fb_url = create_facebook_deep_link(content)
        await update.message.reply_text(
            f"✨ **Предложенный пост:**\n\n{content}",
            reply_markup=get_marketing_keyboard(fb_url)
        )
    except Exception as e:
        logging.error(f"Text error: {e}")
        await update.message.reply_text("❌ Ошибка.")
    finally:
        await status_msg.delete()

    return EDITING_TEXT

async def start_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("✍️ Что именно изменить?")
    return EDITING_TEXT

async def process_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes edits while maintaining the CURRENT context only."""
    user_instruction = update.message.text
    image_path = context.user_data.get('last_image_path')
    last_content = context.user_data.get('last_content', "")
    
    status_msg = await update.message.reply_text("🔄 Обновляю...")
    try:
        content = analyze_mechanic_work(image_path, instruction=user_instruction, current_text=last_content)
        context.user_data['last_content'] = content
        fb_url = create_facebook_deep_link(content)
        await update.message.reply_text(f"✨ **Новый вариант:**\n\n{content}", reply_markup=get_marketing_keyboard(fb_url))
    except Exception as e:
        logging.error(f"Edit error: {e}")
    finally:
        await status_msg.delete()
    return EDITING_TEXT

# --- MAIN ---

if __name__ == "__main__":
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    post_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📷 Создать пост$"), start_post_creation),
            MessageHandler(filters.PHOTO, handle_photo),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_only_post)
        ],
        states={
            WAITING_FOR_POST_IMAGE: [
                MessageHandler(filters.PHOTO, handle_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_only_post),
                CallbackQueryHandler(global_ignore, pattern="^ignore_marketing$")
            ],
            EDITING_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_edit),
                CallbackQueryHandler(start_edit, pattern="^edit_post$"),
                CallbackQueryHandler(finish_post, pattern="^finish_post$"),
                CallbackQueryHandler(global_ignore, pattern="^ignore_marketing$")
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(post_conv)

    print("🤖 Manul Garage Bot is LIVE and CLEAN.")
    app.run_polling()