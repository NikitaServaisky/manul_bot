# 🛠️ Development Log & Roadmap

## 📅 Status: 2026-04-06
- **Completed:** - Designed new modular folder structure.
    - Created `keyboards/` directory.
    - Finished `reply_keyboards.py` (Main menu, User selector).
    - Finished `inline_keyboards.py` (Post actions, Role selection).
- **In Progress:** - Migrating "Spaghetti" code from `main.py` to `handlers/admin_handlers.py`.

## 🚀 To-Do List (Next Steps)
1. [ ] Create `handlers/admin_handlers.py` to process `USER_SHARED` data.
2. [ ] Create `handlers/post_handlers.py` to handle AI image/text processing.
3. [ ] Clean up `main.py` to act only as an entry point.
4. [ ] Update `Dockerfile` to ensure `python-telegram-bot>=20.0`.