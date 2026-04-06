import os
import logging
import time
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
    ConversationHandler,
)
from dotenv import load_dotenv

# Modular Services
from core.auth_service import is_user_authorized, add_user, get_user_role
from services.ai_logic import analyze_mechanic_work
from core.utils import create_facebook_deep_link, escape_md
from core.database import get_db

load_dotenv()

# Logger Setup
logging.basicConfig(level=logging.INFO, format="%(message)s")

# States for ConversationHandlers
EDITING_TEXT = 1
ADDING_USER_ROLE = 2
WAITING_FOR_POST_IMAGE = 3

# Admin ID from .env
ADMIN_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

# --- SECURITY MIDDLEWARE ---
def restricted(func):
    """Decorator checking if user is authorized."""
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID and not is_user_authorized(user_id):
            logging.warning(f"Unauthorized access by {user_id}")
            if update.message:
                await update.message.reply_text("❌ Нет доступа. / No access.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

# --- KEYBOARDS ---

def get_main_menu_keyboard(user_id):
    role = get_user_role(user_id)
    buttons = [[KeyboardButton("📷 Создать пост")]]
    if user_id == ADMIN_ID or role == "owner":
        buttons.append([KeyboardButton("➕ Добавить пользователя")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_marketing_keyboard(fb_url):
    keyboard = [
        [InlineKeyboardButton("🚀 Publish (Facebook)", url=fb_url)],
        [InlineKeyboardButton("✍️ Edit (Изменить)", callback_data="edit_post")],
        [InlineKeyboardButton("✅ Готово (Finish)", callback_data="finish_post")],
        [InlineKeyboardButton("❌ Ignore (Удалить)", callback_data="ignore_marketing")],
    ]
    return InlineKeyboardMarkup(keyboard)

# --- HANDLERS ---

@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        "Добро пожаловать в Manul Garage! 🛠️",
        reply_markup=get_main_menu_keyboard(user_id),
    )

async def global_ignore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text("❌ Процесс отменен.")
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Возвращаюсь в главное меню... 🛠️",
        reply_markup=get_main_menu_keyboard(user_id),
    )
    return ConversationHandler.END

async def finish_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text("✅ Пост завершен!")
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Отлично! Вы в главном меню.",
        reply_markup=get_main_menu_keyboard(user_id),
    )
    return ConversationHandler.END

@restricted
async def start_post_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("📷 Отправьте фото или опишите работу текстом.")
    return WAITING_FOR_POST_IMAGE

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    user_id = update.effective_user.id
    image_path = f"uploads/m_{user_id}_{int(time.time())}.jpg"
    os.makedirs("uploads", exist_ok=True)
    try:
        photo_file = await update.message.photo[-1].get_file()
        await photo_file.download_to_drive(image_path)
        context.user_data["last_image_path"] = image_path
        status_msg = await update.message.reply_text("🛠️ Генерирую пост...")
        content = analyze_mechanic_work(image_path)
        context.user_data["last_content"] = content
        await update.message.reply_text(
            f"✨ **Предложенный пост:**\n\n{content}",
            reply_markup=get_marketing_keyboard(create_facebook_deep_link(content)),
        )
        await status_msg.delete()
        return EDITING_TEXT
    except Exception as e:
        await update.message.reply_text("❌ Ошибка.")
        return WAITING_FOR_POST_IMAGE

async def handle_text_only_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    context.user_data.clear()
    status_msg = await update.message.reply_text("✍️ Готовлю пост...")
    try:
        content = analyze_mechanic_work(None, instruction=user_text)
        context.user_data["last_content"] = content
        await update.message.reply_text(
            f"✨ **Предложенный пост:**\n\n{content}",
            reply_markup=get_marketing_keyboard(create_facebook_deep_link(content)),
        )
    except Exception as e:
        await update.message.reply_text("❌ Ошибка.")
    finally:
        await status_msg.delete()
    return EDITING_TEXT

async def start_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("✍️ Что именно изменить?")
    return EDITING_TEXT

async def process_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_instruction = update.message.text
    image_path = context.user_data.get("last_image_path")
    last_content = context.user_data.get("last_content", "")
    status_msg = await update.message.reply_text("🔄 Обновляю...")
    try:
        content = analyze_mechanic_work(image_path, instruction=user_instruction, current_text=last_content)
        context.user_data["last_content"] = content
        await update.message.reply_text(
            f"✨ **Новый вариант:**\n\n{content}",
            reply_markup=get_marketing_keyboard(create_facebook_deep_link(content)),
        )
    except Exception as e:
        logging.error(f"Edit error: {e}")
    finally:
        await status_msg.delete()
    return EDITING_TEXT

@restricted
async def start_add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👤 Введите Telegram ID нового пользователя:")
    return ADDING_USER_ROLE

@restricted
async def process_add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_id = int(update.message.text)
        add_user(new_id, role="mechanic")
        await update.message.reply_text(f"✅ Пользователь {new_id} добавлен!", 
                                       reply_markup=get_main_menu_keyboard(update.effective_user.id))
    except:
        await update.message.reply_text("❌ Ошибка. Введите числовой ID.")
    return ConversationHandler.END

# --- MAIN ---

if __name__ == "__main__":
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    admin_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ Добавить пользователя$"), start_add_user)],
        states={ADDING_USER_ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_add_user)]},
        fallbacks=[CommandHandler("cancel", global_ignore)],
    )

    post_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📷 Создать пост$"), start_post_creation),
            MessageHandler(filters.PHOTO, handle_photo),
        ],
        states={
            WAITING_FOR_POST_IMAGE: [
                MessageHandler(filters.PHOTO, handle_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_only_post),
            ],
            EDITING_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_edit),
                CallbackQueryHandler(start_edit, pattern="^edit_post$"),
                CallbackQueryHandler(finish_post, pattern="^finish_post$"),
                CallbackQueryHandler(global_ignore, pattern="^ignore_marketing$"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(admin_conv)
    app.add_handler(post_conv)

    print("🤖 Manul Garage Bot is LIVE and SECURE.")
    app.run_polling()