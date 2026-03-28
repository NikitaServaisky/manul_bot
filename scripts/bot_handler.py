import os
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

# Clean Imports - Using our Modular Services
from services.auth_service import is_user_authorized
from services.ai_logic import analyze_mechanic_work
from core.utils import create_facebook_deep_link
from core.database import get_db

load_dotenv()

# Logger Setup
logging.basicConfig(level=logging.INFO, format='%(message)s')

# State for ConversationHandler
EDITING_TEXT = 1

def get_marketing_keyboard(fb_url):
    """Generates the inline keyboard for marketing actions."""
    keyboard = [
        [InlineKeyboardButton("🚀 Publish (Facebook)", url=fb_url)],
        [InlineKeyboardButton("✍️ Edit Post", callback_data="edit_post")],
        [InlineKeyboardButton("❌ Ignore", callback_data="ignore_marketing")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- CONVERSATION FUNCTIONS FOR EDITING ---

async def start_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the edit conversation when 'Edit' is clicked."""
    query = update.callback_query
    await query.answer()
    
    if 'last_image_path' not in context.user_data:
        await query.message.reply_text("❌ Context lost. Please upload a new photo.")
        return ConversationHandler.END
        
    await query.message.reply_text("✍️ What would you like to change? (e.g., 'Make it shorter')")
    return EDITING_TEXT

async def process_edit_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes the text input and calls AI Service again."""
    user_instruction = update.message.text
    image_path = context.user_data.get('last_image_path')

    status_msg = await update.message.reply_text("🔄 Updating post...")

    try:
        # Using the clean service
        new_content = analyze_mechanic_work(image_path, instruction=user_instruction)
        fb_url = create_facebook_deep_link(new_content)
        
        await update.message.reply_text(
            f"✨ **Updated Version:**\n\n{new_content}",
            reply_markup=get_marketing_keyboard(fb_url)
        )
        await status_msg.delete()
    except Exception as e:
        logging.error(f"Edit Error: {e}")
        await update.message.reply_text("❌ Error during update.")

    return ConversationHandler.END

# --- NORMAL HANDLERS ---

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles button interactions (Accept/Ignore)."""
    query = update.callback_query
    await query.answer() 
    
    if query.data in ["ignore", "ignore_marketing"]:
        await query.edit_message_text(text=f"{query.message.text}\n\n❌ Status: Ignored")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes incoming photos for marketing content."""
    user_id = update.message.from_user.id
    
    # 1. Check Authorization via Service
    if not is_user_authorized(user_id):
        await update.message.reply_text("⛔ Access Denied.")
        return
    
    # 2. Prepare file path
    timestamp = int(time.time())
    image_path = os.path.join("uploads", f"marketing_{user_id}_{timestamp}.jpg")

    try:
        photo_file = await update.message.photo[-1].get_file()
        await photo_file.download_to_drive(image_path)
        
        context.user_data['last_image_path'] = image_path
        status_msg = await update.message.reply_text("🛠️ Generating marketing post...")
        
        # 3. Call AI Logic Service
        marketing_content = analyze_mechanic_work(image_path)
        
        # 4. Save to DB using Centralized Connection
        with get_db() as conn:
            conn.execute(
                "INSERT INTO marketing_posts (image_path, generated_content, user_id) VALUES (?, ?, ?)", 
                (image_path, marketing_content, user_id)
            )
            conn.commit()

        fb_url = create_facebook_deep_link(marketing_content)
        await update.message.reply_text(
            f"✨ **Suggested Post:**\n\n{marketing_content}",
            reply_markup=get_marketing_keyboard(fb_url)
        )
        await status_msg.delete()
    except Exception as e:
        logging.error(f"Photo processing error: {e}")
        await update.message.reply_text("❌ Something went wrong.")

if __name__ == "__main__":
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    # Conversation for Editing
    edit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_edit, pattern="^edit_post$")],
        states={
            EDITING_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_edit_request)],
        },
        fallbacks=[CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^ignore_marketing$")],
    )

    app.add_handler(edit_conv)
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("🤖 Bot is live and clean.")
    app.run_polling()