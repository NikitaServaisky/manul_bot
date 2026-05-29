from telegram.ext import ConversationHandler, MessageHandler, CallbackQueryHandler, CommandHandler, filters
import handlers.admin_callbacks as cb

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
    entry_points=[MessageHandler(filters.Regex("^➕ Добавить сотрудника$"), cb.start_add_user_flow)],
    states={
        ADDING_USER_FLOW: [
            MessageHandler(filters.StatusUpdate.USERS_SHARED, cb.process_user_shared),
        ],
        WAITING_FOR_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, cb.process_user_name)],
        WAITING_FOR_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, cb.process_user_id_number)],
        
        # Added CallbackQueryHandler to catch the "skip_phone" button action
        WAITING_FOR_PHONE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, cb.process_user_phone),
            CallbackQueryHandler(cb.process_user_phone, pattern="^skip_phone$")
        ],
        
        # Bank registration state routing with text inputs and skip buttons paired
        WAITING_FOR_BANK_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, cb.process_bank_name),
            CallbackQueryHandler(cb.process_bank_name, pattern="^skip_bank$")
        ],
        WAITING_FOR_BANK_BRANCH: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, cb.process_bank_branch),
            CallbackQueryHandler(cb.process_bank_branch, pattern="^skip_branch$")
        ],
        WAITING_FOR_BANK_ACCOUNT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, cb.process_bank_account),
            CallbackQueryHandler(cb.process_bank_account, pattern="^skip_account$")
        ],
        
        # Fixed pattern to match your optimized inline keyboard ('salary_hourly' / 'salary_monthly')
        WAITING_FOR_SALARY_TYPE: [
            CallbackQueryHandler(cb.process_salary_type, pattern="^salary_")
        ],
        
        WAITING_FOR_RATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, cb.process_salary_rate)],
        WAITING_FOR_ROLE: [
            CallbackQueryHandler(cb.handel_role_callback, pattern="^setrole_"),
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cb.cancel_admin_flow),
        MessageHandler(filters.Regex("^❌ Отмена$") | filters.COMMAND, cb.cancel_admin_flow)
    ],
)