# ---- External imports ---- #
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_post_confirmation_keyboard(fb_url):
    """
    Buttons that appermunder the AI-generated post.
    """
    keyboard = [
        # Button 1: Deep link to Facebook with the text
        [InlineKeyboardButton("🚀 Опубликовать (Facebook)", url=fb_url)],
        # Button 2: Edit the taxt if the AI a mistake
        [InlineKeyboardButton("✍️ Редактировать", callback_data="edit_post")],
        # Button 3: Finish and return to main menu
        [InlineKeyboardButton("✅ Готово", callback_data="finish_post")],
        # Button 4: Delete/Cancel this post
        [InlineKeyboardButton("❌ Удалить", callback_data="ignore_post")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_role_selection_keyboard(target_id):
    """
    Buttons for the Admin to choose a role for the new employee
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "👨‍🔧 Механик", callback_data=f"setrole_{target_id}_mechanic"
            ),
            InlineKeyboardButton(
                "👑 Владелец", callback_data=f"setrole_{target_id}_owner"
            ),
        ],
        [InlineKeyboardButton("🚫 Отмена", callback_data="cancel_auth")],
    ]
    return InlineKeyboardMarkup(keyboard)
