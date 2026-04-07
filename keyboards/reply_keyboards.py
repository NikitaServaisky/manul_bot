from telegram import ReplyKeyboardMarkup, KeyboardButton, KeyboardButtonRequestUsers

def get_main_menu(user_id, admin_id, role):
    """
    Main menu keyboard logic:
    - Mechanics: Can only create posts.
    - Owners/Admin: Can create posts AND employees
    """
    # Evryone can create posts
    buttons = [[KeyboardButton("📷 Создать пост")]]

    # Only Owner or Admin see "add employees" button
    if user_id == admin_id or role == "owner":
        buttons.append([KeyboardButton("➕ Добавить сотрудника")])

        return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_user_selector_keyboard():
    """ Keyboard for selecting a user from Telegram contacts."""
    buttons = [
        [KeyboardButton(
            text="👤 Выбрать сотрудника",
            request_users=KeyboardButtonRequestUsers(
                request_id=1,
                user_is_bot=False,
                max_quantity=1
            )
        )],
        [KeyboardButton("🔙 Отмена")],
    ]
    return ReplyKeyboardMarkup(buttons,resize_keyboard=True, one_time_keyboard=True)