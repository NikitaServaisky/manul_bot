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
from scripts.hunter import run_hunt

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
    
    # Only Admin or Owners can see the "Add User" button
    if user_id == ADMIN_ID or role == 'owner':
        buttons.append([KeyboardButton("➕ Добавить пользователя")])
        
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_marketing_keyboard(fb_url):
    """Inline keyboard for post actions."""
    keyboard = [
        [InlineKeyboardButton("🚀 Publish (Facebook)", url=fb_url)],
        [InlineKeyboardButton("✍️ Edit Post", callback_data="edit_post")],
        [InlineKeyboardButton("✅ Готово (Finish)", callback_data="finish_post")],
        [InlineKeyboardButton("❌ Ignore", callback_data="ignore_marketing")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- START & AUTH HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initializes the bot and shows the main menu."""
    user_id = update.effective_user.id
    await update.message.reply_text(
        "Добро пожаловать в Manul Garage! 🛠️",
        reply_markup=get_main_menu_keyboard(user_id)
    )

# --- POST CREATION FLOW (The New Logic) ---

async def start_post_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggered by 'Создать пост'. Asks for photo."""
    await update.message.reply_text("📷 Пожалуйста, отправьте фотографию для нового поста.")
    return WAITING_FOR_POST_IMAGE

# --- ADD USER CONVERSATION ---

async def start_add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggered by the 'Add User' button. Asks for a contact."""
    user_id = update.effective_user.id
    role = get_user_role(user_id)
    
    if user_id != ADMIN_ID and role != 'owner':
        return ConversationHandler.END

    contact_btn = [[KeyboardButton("Выбрать из контактов", request_contact=True)]]
    await update.message.reply_text(
        "Пожалуйста, выберите контакт из списка вашего телефона:",
        reply_markup=ReplyKeyboardMarkup(contact_btn, resize_keyboard=True, one_time_keyboard=True)
    )
    return ADDING_USER_ROLE

async def handle_contact_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes the shared contact and asks for a role."""
    contact = update.message.contact
    new_user_id = contact.user_id
    new_name = contact.first_name

    if not new_user_id:
        await update.message.reply_text("❌ Этот пользователь должен быть в Telegram.", reply_markup=get_main_menu_keyboard(update.effective_user.id))
        return ConversationHandler.END

    # Temporary storage for the callback
    context.user_data['pending_user'] = {'id': new_user_id, 'name': new_name}

    keyboard = [
        [InlineKeyboardButton("Владелец (Owner)", callback_data="role_owner")],
        [InlineKeyboardButton("Сотрудник (Staff)", callback_data="role_staff")]
    ]
    await update.message.reply_text(
        f"Какую роль назначить для {new_name}?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ADDING_USER_ROLE

async def finalize_user_addition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves the user to DB after role is selected."""
    query = update.callback_query
    await query.answer()
    
    role = "owner" if "owner" in query.data else "staff"
    user_data = context.user_data.get('pending_user')

    if user_data:
        add_user(user_data['id'], user_data['name'], role)
        await query.edit_message_text(f"✅ Пользователь {user_data['name']} добавлен как {role}.")
    
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Готово! Вы в главном меню.",
        reply_markup=get_main_menu_keyboard(update.effective_user.id)
    )
    return ConversationHandler.END

# --- POST CREATION & EDITING ---

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes incoming photos for marketing content."""
    user_id = update.effective_user.id
    if not is_user_authorized(user_id):
        await update.message.reply_text("⛔ Доступ запрещен.")
        return

    image_path = f"uploads/m_{user_id}_{int(time.time())}.jpg"
    os.makedirs("uploads", exist_ok=True)

    try:
        photo_file = await update.message.photo[-1].get_file()
        await photo_file.download_to_drive(image_path)
        context.user_data['last_image_path'] = image_path
        
        status_msg = await update.message.reply_text("🛠️ Генерирую пост...")
        content = analyze_mechanic_work(image_path)

        # Save contatext in the cache
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
        await update.message.reply_text("❌ Произошла ошибка.")

async def start_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("✍️ Что вы хотите изменить? (Например: 'Сделай текст короче')")
    return EDITING_TEXT

async def process_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_instruction = update.message.text
    image_path = context.user_data.get('last_image_path')
    last_content = context.user_data.get('last_content', "")
    
    status_msg = await update.message.reply_text("🔄 Обновляю...")
    content = analyze_mechanic_work(image_path, instruction=user_instruction, current_text=last_content)
    context.user_data['last_content'] = content
    fb_url = create_facebook_deep_link(content)
    
    await update.message.reply_text(f"✨ **Новый вариант:**\n\n{content}", reply_markup=get_marketing_keyboard(fb_url))
    await status_msg.delete()
    return  EDITING_TEXT

async def finish_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()

    await query.edit_message_text("✅ Пост готов и сохранен!")
    
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Отлично!",
        reply_markup=get_main_menu_keyboard(user_id)
    )
    return ConversationHandler.END

# --- MAIN ---

if __name__ == "__main__":
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # 0. Define global_ignore FIRST so other handlers can use it
    async def global_ignore(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = update.effective_user.id
        await query.answer()
        
        # Edit message to show it was deleted
        await query.edit_message_text("❌ Пост удален из системы.")

        # Send a new message to bring backthe main keyboard
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Возвращаюсь в главное меню... 🛠️",
            reply_markup=get_main_menu_keyboard(user_id)
        )
        return ConversationHandler.END

    # 1. Add User Conversation
    add_user_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ Добавить пользователя$"), start_add_user)],
        states={
            ADDING_USER_ROLE: [
                MessageHandler(filters.CONTACT, handle_contact_received),
                CallbackQueryHandler(finalize_user_addition, pattern="^role_")
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    # 2. Post Creation & Editing Conversation (Unified flow)
    post_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📷 Создать пост$"), start_post_creation),
            CallbackQueryHandler(start_edit, pattern="^edit_post$")
        ],
        states={
            WAITING_FOR_POST_IMAGE: [
                MessageHandler(filters.PHOTO, handle_photo),
                CallbackQueryHandler(start_edit, pattern="^edit_post$"),
                CallbackQueryHandler(global_ignore, pattern="^ignore_marketing$")
            ],
            EDITING_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_edit),
                CallbackQueryHandler(start_edit, pattern="^edit_post$"),
                CallbackQueryHandler(finish_post, pattern="^finish_post$"), # כפתור סיום
                CallbackQueryHandler(global_ignore, pattern="^ignore_marketing$")
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            CallbackQueryHandler(global_ignore, pattern="^ignore_marketing$")
        ],
        allow_reentry=True
    )

    # Registering all handlers to the application
    app.add_handler(CommandHandler("start", start))
    app.add_handler(add_user_conv)
    app.add_handler(post_conv)
    
    # Standalone ignore handler for cases outside the conversation
    app.add_handler(CallbackQueryHandler(global_ignore, pattern="^ignore_marketing$"))

    # --- Hunter Configuration ---
    HUNTER_ACTIVE = False 

    if app.job_queue:
        if HUNTER_ACTIVE:
            app.job_queue.run_repeating(run_hunt, interval=3600, first=10)
            print("✅ [STATUS] Lead Hunter is ACTIVE.")
        else:
            print("ℹ️ [STATUS] Lead Hunter is DISABLED.")

    print("🤖 Bot is live and fixed! Ready for testing.")
    app.run_polling()