from telegram.ext import ConversationHandler, MessageHandler, CallbackQueryHandler, CommandHandler, filters
from src.bot.callbacks.admin import (
    start_add_user_flow,
    _handle_optional_input,
    process_user_shared,
    process_user_name,
    process_user_id_number,
    process_user_phone,
    process_bank_name,
    process_bank_branch,
    process_bank_account,
    process_salary_type,
    process_salary_rate,
    handel_role_callback,
    cancel_admin_flow
)

# Updated Conversation States Matching the Callbacks
(
    ADDING_USER_FLOW,
    WAITING_FOR_NAME,
    WAITING_FOR_ID,
    WAITING_FOR_PHONE,
    WAITING_FOR_BANK_NAME,
    WAITING_FOR_BANK_BRANCH,
    WAITING_FOR_BANK_ACCOUNT,
    WAITING_FOR_SALARY_TYPE,
    WAITING_FOR_RATE,
    WAITING_FOR_ROLE 
) = range(1, 11)

admin_conv = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^➕ Добавить сотрудника$"), start_add_user_flow)],
    states={
        ADDING_USER_FLOW: [
            MessageHandler(filters.StatusUpdate.USERS_SHARED, process_user_shared),
        ],
        WAITING_FOR_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_user_name)],
        WAITING_FOR_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_user_id_number)],
        
        # Added CallbackQueryHandler to catch the "skip_phone" button action
        WAITING_FOR_PHONE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_user_phone),
            CallbackQueryHandler(process_user_phone, pattern="^skip_phone$")
        ],
        
        # Bank registration state routing with text inputs and skip buttons paired
        WAITING_FOR_BANK_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_bank_name),
            CallbackQueryHandler(process_bank_name, pattern="^skip_bank$")
        ],
        WAITING_FOR_BANK_BRANCH: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_bank_branch),
            CallbackQueryHandler(process_bank_branch, pattern="^skip_branch$")
        ],
        WAITING_FOR_BANK_ACCOUNT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_bank_account),
            CallbackQueryHandler(process_bank_account, pattern="^skip_account$")
        ],
        
        # Fixed pattern to match your optimized inline keyboard ('salary_hourly' / 'salary_monthly')
        WAITING_FOR_SALARY_TYPE: [
            CallbackQueryHandler(process_salary_type, pattern="^salary_")
        ],
        
        WAITING_FOR_RATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_salary_rate)],
        WAITING_FOR_ROLE: [
            CallbackQueryHandler(handel_role_callback, pattern="^setrole_"),
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel_admin_flow),
        MessageHandler(filters.Regex("^❌ Отмена$") | filters.COMMAND, cancel_admin_flow)
    ],
)