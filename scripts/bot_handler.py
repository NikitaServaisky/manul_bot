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
ADDING_USER_FLOW = 2
WAITING_FOR_POST_IMAGE = 3

# Admin ID from .env
ADMIN_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

# --- SECURITY MIDDLEWARE ---

def restricted(func):
    """Decorator to restrict access to authorized users only."""
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID and not is_user_authorized(user_id):
            logging.warning(f"Unauthorized access attempt by {user_id}")
            if update.message:
                await update.message.reply_text("❌ Нет доступа. Обратитесь к администратору.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

# --- KEYBOARDS (All UI in Russian) ---

def get_main_menu_keyboard(user_id):
    """Main persistent keyboard."""
    role = get_user_role(user_id)
    buttons = [[KeyboardButton("📷 Создать пост")]]
    
    if user_id == ADMIN_ID or role == "owner":
        buttons.append([KeyboardButton("➕ Добавить сотрудника")])
    
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_contact_request_keyboard():
    """Keyboard to request contact from phonebook."""
    buttons = [
        [KeyboardButton("👤 Выбрать из контактов", request_contact=True)],
        [KeyboardButton("🔙 Отмена")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)

def get_marketing_keyboard(fb_url):
    """Inline keyboard for post actions."""
    keyboard = [
        [InlineKeyboardButton("🚀 Опубликовать (Facebook)", url=fb_url)],
        [InlineKeyboardButton("✍️ Редактировать", callback_data="edit_post")],
        [InlineKeyboardButton("✅ Готово", callback_data="finish_post")],
        [InlineKeyboardButton("❌ Удалить", callback_data="ignore_marketing")],
    ]
    return InlineKeyboardMarkup(keyboard)

# --- HANDLERS ---

@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Standard start command."""
    user_id = update.effective_user.id
    await update.message.reply_text(
        "Добро пожаловать в Manul Garage! 🛠️",
        reply_markup=get_main_menu_keyboard(user_id),
    )

@restricted
async def start_add_user_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: Ask for contact from the admin."""
    await update.message.reply_text(
        "Пожалуйста, выберите сотрудника из вашего списка контактов:",
        reply_markup=get_contact_request_keyboard()
    )
    return ADDING_USER_FLOW

@restricted
async def process_contact_addition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: Receive contact and ask for role assignment."""
    contact = update.message.contact
    if not contact or not contact.user_id:
        await update.message.reply_text(
            "❌ Этот контакт не использует Telegram или данные скрыты. Введите ID вручную или попробуйте другой контакт.",
            reply_markup=get_main_menu_keyboard(update.effective_user.id)
        )
        return ConversationHandler.END

    target_id = contact.user_id
    name = contact.first_name

    keyboard = [
        [
            InlineKeyboardButton("👨‍🔧 Механик", callback_data=f"setrole_{target_id}_mechanic"),
            InlineKeyboardButton("👑 Владелец", callback_data=f"setrole_{target_id}_owner")
        ]
    ]
    
    await update.message.reply_text(
        f"Какую роль назначить для {name} (ID: {target_id})?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END

async def handle_role_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 3: Save user to DB via Inline Button."""
    query = update.callback_query
    await query.answer()
    
    # Data format: setrole_{id}_{role}
    _, target_id, role = query.data.split("_")
    
    add_user(int(target_id), role=role)
    
    await query.edit_message_text(f"✅ Пользователь {target_id} успешно добавлен как {role}!")
    
    # Notify the new user
    try:
        await context.bot.send_message(
            chat_id=int(target_id),
            text=f"🎉 Вам открыт доступ к Manul Garage! Ваша роль: {role}. Нажмите /start",
        )
    except Exception:
        logging.warning(f"Could not notify user {target_id}")

# --- POST CREATION LOGIC ---

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
            f"✨ **Ваш пост:**\n\n{content}",
            reply_markup=get_marketing_keyboard(create_facebook_deep_link(content)),
        )
        await status_msg.delete()
        return EDITING_TEXT
    except Exception as e:
        await update.message.reply_text("❌ Ошибка обработки фото.")
        return WAITING_FOR_POST_IMAGE

async def handle_text_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    context.user_data.clear()
    status_msg = await update.message.reply_text("✍️ Готовлю текст...")
    try:
        content = analyze_mechanic_work(None, instruction=user_text)
        context.user_data["last_content"] = content
        await update.message.reply_text(
            f"✨ **Ваш пост:**\n\n{content}",
            reply_markup=get_marketing_keyboard(create_facebook_deep_link(content)),
        )
    except Exception:
        await update.message.reply_text("❌ Ошибка AI.")
    finally:
        await status_msg.delete()
    return EDITING_TEXT

async def global_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels any process and returns to menu."""
    user_id = update.effective_user.id
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("❌ Отменено.")
    else:
        await update.message.reply_text("❌ Отменеנו.")
        
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Возврат в меню...",
        reply_markup=get_main_menu_keyboard(user_id)
    )
    return ConversationHandler.END

# --- MAIN EXECUTION ---

if __name__ == "__main__":
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # Conversation for adding users via contacts
    admin_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ Добавить сотрудника$"), start_add_user_flow)],
        states={
            ADDING_USER_FLOW: [
                MessageHandler(filters.CONTACT, process_contact_addition),
                MessageHandler(filters.Regex("^🔙 Отмена$"), global_cancel)
            ],
        },
        fallbacks=[CommandHandler("cancel", global_cancel)],
    )

    # Conversation for creating posts
    post_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📷 Создать пост$"), start_post_creation),
            MessageHandler(filters.PHOTO, handle_photo),
        ],
        states={
            WAITING_FOR_POST_IMAGE: [
                MessageHandler(filters.PHOTO, handle_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_post),
            ],
            EDITING_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, analyze_mechanic_work), # Simplified for now
                CallbackQueryHandler(global_cancel, pattern="^ignore_marketing$"),
                CallbackQueryHandler(global_cancel, pattern="^finish_post$"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(admin_conv)
    app.add_handler(post_conv)
    app.add_handler(CallbackQueryHandler(handle_role_callback, pattern="^setrole_"))

    print("🤖 Manul Garage Bot is LIVE (Russian UI / Contact Integration)")
    app.run_polling()