import os
from telegram import ReplyKeyboardMarkup, KeyboardButton, KeyboardButtonRequestUsers
from core.auth_service import get_user_role

def get_main_menu(user_id):
    """
    Main menu keyboard logic:
    - Mechanics: Can only create posts.
    - Owners/Admin: Can create posts AND employees
    """
    # Everyone can create posts
    buttons = [
        [KeyboardButton("📷 Создать пост")],
        [KeyboardButton("➕ Добавить автомобиль")]
    ]

    role = get_user_role(user_id)
    ADMIN_ID = int(os.getenv("TELEGRAM_CHAT_ID", 0))

    # Only Owner or Admin see "add employees" button
    if user_id == ADMIN_ID or role == "owner":
        buttons.append([KeyboardButton("➕ Добавить сотрудника")])

    # Out of the IF scope, so mechanics get their layout properly
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def get_user_selector_keyboard():
    """Keyboard for selecting a user from Telegram contacts."""
    buttons = [
        [
            KeyboardButton(
                text="👤 Выбрать сотрудника",
                request_users=KeyboardButtonRequestUsers(
                    request_id=1, user_is_bot=False, max_quantity=1
                ),
            )
        ],
        [KeyboardButton("🔙 Отмена")],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)