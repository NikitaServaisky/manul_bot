import os
import logging
import time
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    KeyboardButtonRequestUsers, # Required for user selection
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

# Modular Services (Ensure these files exist in your project structure)
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
    """Decorator to restrict access to the Admin and authorized users only."""
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID and not is_user_authorized(user_id):
            logging.warning(f"Unauthorized access attempt by {user_id}")
            if update.message:
                await update.message.reply_text("❌ Нет доступа. Обратитесь к Никите.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

# --- KEYBOARDS (Russian UI) ---

def get_main_menu_keyboard(user_id):
    """Main persistent menu based on user role."""
    role = get_user_role(user_id)
    buttons = [[KeyboardButton("📷 Создать пост")]]
    
    if user_id == ADMIN_ID or role == "owner":
        buttons.append([KeyboardButton("➕ Добавить сотрудника")])
    
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_user_selection_keyboard():
    """Keyboard that triggers the Telegram user picker."""
    buttons = [
        [KeyboardButton(
            text="👤 Выбрать сотрудника", 
            request_users=KeyboardButtonRequestUsers(
                request_id=1, 
                user_is_bot=False, 
                max_quantity=1
            )
        )],
        [KeyboardButton("🔙 Отмена")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)

def get_marketing_keyboard(fb_url):
    """Inline keyboard for post management."""
    keyboard = [
        [InlineKeyboardButton("🚀 Опубликовать (Facebook)", url=fb_url)],
        [InlineKeyboardButton("✍️ Редактировать", callback_data="edit_post")],
        [InlineKeyboardButton("✅ Готово", callback_data="finish_post")],
        [InlineKeyboardButton("❌ Удалить", callback_data="ignore_marketing")],
    ]
    return InlineKeyboardMarkup(keyboard)

# --- AUTH & USER MANAGEMENT ---

@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Standard /start command."""
    user_id = update.effective_user.id
    await update.message.reply_text(
        "Добро пожаловать в Manul Garage! 🛠️",
        reply_markup=get_main_menu_keyboard(user_id),
    )

@restricted
async def start_add_user_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: Prompt admin to select a user from Telegram list."""
    await update.message.reply_text(
        "Нажмите кнопку ниже, чтобы выбрать сотрудника из списка контактов:",
        reply_markup=get_user_selection_keyboard()
    )
    return ADDING_USER_FLOW

@restricted
async def process_user_shared(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: Handle the shared user data and ask for role."""
    shared_user = update.message.user_shared
    if not shared_user:
        await update.message.reply_text("❌ Ошибка выбора. Попробуйте еще раз.")
        return ConversationHandler.END

    target_id = shared_user.user_ids[0]
    
    keyboard = [
        [
            InlineKeyboardButton("👨‍🔧 Механик", callback_data=f"setrole_{target_id}_mechanic"),
            InlineKeyboardButton("👑 Владелец", callback_data=f"setrole_{target_id}_owner")
        ]
    ]
    
    await update.message.reply_text(
        f"Пользователь выбран (ID: {target_id}). Какую роль ему назначить?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END

async def handle_role_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 3: Save user to DB and return to main menu."""
    query = update.callback_query
    admin_id = update.effective_user.id
    await query.answer()
    
    # Parse callback: setrole_{id}_{role}
    _, target_id, role = query.data.split("_")
    
    add_user(int(target_id), role=role)
    
    await query.edit_message_text(f"✅ Пользователь {target_id} добавлен как {role}!")
    
    # Return to main menu with keyboard
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Готово! Возвращаюсь в главное меню. 🛠️",
        reply_markup=get_main_menu_keyboard(admin_id)
    )
    
    # Notify the new user if possible
    try:
        await context.bot.send_message(
            chat_id=int(target_id),
            text=f"🎉 Вам открыт доступ к Manul Garage! Роль: {role}. Нажмите /start",
        )
    except Exception:
        pass

# --- POST CREATION ---

@restricted
async def start_post_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initiates post creation flow."""
    context.user_data.clear()
    await update.message.reply_text("📷 Отправьте фото или опишите работу текстом.")
    return WAITING_FOR_POST_IMAGE

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles photo input and generates AI post."""
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
    except Exception:
        await update.message.reply_text("❌ Ошибка при обработке фото.")
        return WAITING_FOR_POST_IMAGE

async def handle_text_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles text-only input and generates AI post."""
    user_text = update.message.text
    context.user_data.clear()
    status_msg = await update.message.reply_text("✍️ Готовлю текст...")
    try:
        content = analyze_mechanic_work(None, instruction=user_text)
        context.user_data["last_content"] = content
        await update.message.reply_text(
            f"✨ **Ваш post:**\n\n{content}",
            reply_markup=get_marketing_keyboard(create_facebook_deep_link(content)),
        )
    except Exception:
        await update.message.reply_text("❌ Ошибка AI.")
    finally:
        await status_msg.delete()
    return EDITING_TEXT

async def global_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels current operation and returns to main menu."""
    user_id = update.effective_user.id
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("❌ Отменено.")
    else:
        await update.message.reply_text("❌ Отменено.")
        
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Меню:",
        reply_markup=get_main_menu_keyboard(user_id)
    )
    return ConversationHandler.END

# --- APP SETUP ---

if __name__ == "__main__":
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    # User Management Conversation
    admin_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ Добавить сотрудника$"), start_add_user_flow)],
        states={
            ADDING_USER_FLOW: [
                MessageHandler(filters.StatusUpdate.USER_SHARED, process_user_shared),
                MessageHandler(filters.Regex("^🔙 Отмена$"), global_cancel)
            ],
        },
        fallbacks=[CommandHandler("cancel", global_cancel)],
    )

    # Content Creation Conversation
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
                CallbackQueryHandler(global_cancel, pattern="^ignore_marketing$"),
                CallbackQueryHandler(global_cancel, pattern="^finish_post$"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    # Handlers Registration
    app.add_handler(CommandHandler("start", start))
    app.add_handler(admin_conv)
    app.add_handler(post_conv)
    app.add_handler(CallbackQueryHandler(handle_role_callback, pattern="^setrole_"))

    print("🤖 Manul Garage Bot is RUNNING with Contact Integration.")
    app.run_polling()