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
        [InlineKeyboardButton("🚫 Отмена", callback_data="cancel_admin")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_salary_type_keyboard():
    """Generate a kyeboard for selecting the employee's a salary type."""
    keyboard = [
        [
            InlineKeyboardButton(
                "Почасовая (hourly)", callback_data="salary_hourly"
            ),
            InlineKeyboardButton(
                "Оклад (monthly)", callback_data="salary_monthly"
            ),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_skip_keyboard(step_name: str):
    """ Generates a standalone skip button for optional filds."""
    keyboard = [[
        InlineKeyboardButton("⏩ Пропустить", callback_data=f"skip_{step_name}")
    ]]
    return InlineKeyboardMarkup(keyboard)

def get_employee_area_keyboard():
    """
    Inline keyboard inside the Employee Personal Area.
    """
    keyboard = [
        # View work schedule
        [InlineKeyboardButton("📅 Мой график (Schedule)", callback_data="emp_schedule")],
        # Request vacation / Submit sick leave
        [
            InlineKeyboardButton("🏖️ Запросить отпуск", callback_data="emp_vacation"),
            InlineKeyboardButton("🤒 Больничный (Sick)", callback_data="emp_sick")
        ],
        # Upload general documents (e.g., Form 101)
        [InlineKeyboardButton("📁 Загрузить документы (Form 101)", callback_data="emp_upload_doc")],
        # Submit shifts / availability for next week
        [InlineKeyboardButton("✍️ Подать смены (Submit Shifts)", callback_data="emp_submit_shifts")]
    ]
    return InlineKeyboardMarkup(keyboard)

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_employee_vacation_confirm_keyboard():
    """Buttons for the employee to review before sending to the manager."""
    keyboard = [
        [
            InlineKeyboardButton("📤 Отправить менеджеру", callback_data="vact_confirm_send"),
            InlineKeyboardButton("✏️ Изменить данные", callback_data="vact_confirm_edit")
        ],
        [InlineKeyboardButton("❌ Отмена", callback_data="vact_confirm_cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_manager_vacation_approval_keyboard(request_id: int):
    """Buttons for the manager to approve or reject a specific vacation ID."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Одобрить отпуск", callback_data=f"vact_mgr_approve_{request_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"vact_mgr_reject_{request_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)