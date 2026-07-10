from telegram.ext import ConversationHandler, MessageHandler, CallbackQueryHandler, filters
from handlers.employee_handlers import open_personal_cabinet, handle_schedule_view

# States for conversation if needed later (e.g., waiting for document upload)
UPLOAD_DOC, VACATION_DATE = range(2)

employee_conv = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Text("💼 Личный кабинет"), open_personal_cabinet)
    ],
    states={
        # כאן תוסיף בהמשך שלבים שדורשים קלט מהמשתמש (כמו העלאת קובץ או הקלדת תאריך)
        # UPLOAD_DOC: [MessageHandler(filters.Document.ALL, save_doc_handler)]
    },
    fallbacks=[
        # sould to cancel the process
        CommandHandler("cancel", open_personal_cabinet) 
    ]
)

schedule_handler = CallbackQueryHandler(handle_schedule_view, pattern="^emp_schedule$")