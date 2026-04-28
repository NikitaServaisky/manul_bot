import os
import time
import logging
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CommandHandler,
    CallbackQueryHandler,
)

# Internal Imports
from keyboards.reply_keyboards import get_main_menu
from keyboards.inline_keyboards import get_post_confirmation_keyboard
from services.ai_logic import analyze_mechanic_work
from core.utils import create_facebook_deep_link

# States for the Post Conversation
WAITING_FOR_CONTENT = 1
EDITING_POST = 2

ADMIN_ID = int(os.getenv("TELEGRAM_CHAT_ID"))


async def start_post_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: User clicks 'Create Post'. Ask for Image or Text."""
    await update.message.reply_text(
        "📷 Отправьте фото работы или просто опишите словами, что вы сделали:",
        reply_markup=None,  # Optional: you can add a 'Cancel' button here
    )
    return WAITING_FOR_CONTENT


async def handle_post_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: Receive Photo or Text and process with AI."""
    user_id = update.effective_user.id
    status_msg = await update.message.reply_text("🛠️ Генерирую пост, подождите...")

    image_path = None
    user_description = update.message.text or update.message.caption

    # Define sub-directory for marketing images
    marketing_dir = os.path.join("uploads", "marketing")

    # Case A: User sent a Photo
    if update.message.photo:
        photo_file = await update.message.photo[-1].get_file()

        # Ensure the sub-directory exists
        os.makedirs(marketing_dir, exist_ok=True)

        # Generate unique filename within the marketing sub-folder
        image_path = os.path.join(
            marketing_dir, f"post_{user_id}_{int(time.time())}.jpg"
        )

        await photo_file.download_to_drive(image_path)

    try:
        # Call your AI service (Gemini/Groq logic)
        ai_generated_text = analyze_mechanic_work(
            image_path, instruction=user_description
        )
        context.user_data["last_post_text"] = ai_generated_text

        # Prepare the Facebook Link
        fb_link = create_facebook_deep_link(ai_generated_text)

        await update.message.reply_text(
            f"✨ **Предложенный текст:**\n\n{ai_generated_text}",
            reply_markup=get_post_confirmation_keyboard(fb_link),
        )
    except Exception as e:
        logging.error(f"AI Error: {e}")
        await update.message.reply_text("❌ Ошибка при генерации. Попробуйте еще раз.")
    finally:
        await status_msg.delete()

    return EDITING_POST


async def cancel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fallback to exit post creation."""
    user_id = update.effective_user.id
    await update.message.reply_text(
        "Создание поста отменено.",
        reply_markup=get_main_menu(user_id, ADMIN_ID, "mechanic"),
    )
    return ConversationHandler.END

async def finish_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ends the conversation and clears user data."""
    query = update.callback_query
    await query.answer()
    
    action = query.data # "finish_post" or "ignore_post"
    
    if action == "finish_post":
        await query.edit_message_text("✅ Пост опубликован (или скопирован)! Удачи!")
    else:
        await query.edit_message_text("🗑️ Пост отклонен.")
        
    # Show main menu again
    user_id = update.effective_user.id
    await context.bot.send_message(
        chat_id=user_id,
        text="Чем еще могу помочь?",
        reply_markup=get_main_menu(user_id, ADMIN_ID, "mechanic")
    )
    return ConversationHandler.END

async def handle_edit_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Asks the user what to change in the text."""
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text(
        "📝 Напишите, что именно нужно изменить в тексте (например: 'сделай короче' или 'добавь цену'):"
    )
    # Go back to WAITING_FOR_CONTENT to process the new instruction
    return WAITING_FOR_CONTENT

# --- POST CONVERSATION DEFINITION ---
post_conv = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^📷 Создать пост$"), start_post_flow)],
    states={
        WAITING_FOR_CONTENT: [
            MessageHandler(
                filters.PHOTO | filters.TEXT & ~filters.COMMAND, handle_post_content
            )
        ],
        EDITING_POST: [
            CallbackQueryHandler(finish_post, pattern="^(finish_post|ignore_post)$"),
            CallbackQueryHandler(handle_edit_request, pattern="^edit_post$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_post_content),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_post)],
)
