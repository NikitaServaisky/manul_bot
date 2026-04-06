# 📘 Learning & Variables Dictionary - Manul Garage Bot

## 🏗️ Project Architecture
The bot uses a **Modular Architecture** to separate concerns:
- `handlers/`: Logic for user interactions (Admin/Post flows).
- `keyboards/`: All UI components (Reply and Inline).
- `core/`: Low-level services (Auth, Database, Utils).

## 🔄 Conversation States
- `ADDING_USER_FLOW`: (admin_handlers.py) Manages the sequence from clicking "Add" to role assignment.
- `WAITING_FOR_CONTENT`: (post_handlers.py) The bot is idle, waiting for the mechanic to send a photo/text.
- `EDITING_POST`: (post_handlers.py) The AI text is generated; waiting for the user to confirm, edit, or delete.

## 🔑 Key Variables & Concepts
- `ADMIN_ID`: The Telegram ID of Nikita. Hardcoded or loaded from `.env` as the primary authority.
- `target_id`: The ID of the employee currently being added. Extracted from the `user_shared` object.
- `role`: Permission level stored in DB:
    - `mechanic`: Can only trigger post creation.
    - `owner`: Can trigger posts AND manage team members.
- `request_users`: Telegram API v6.7 tool. Opens the native contact picker for high security and UX.
- `callback_data`: The hidden string behind Inline Buttons (e.g., `setrole_123_mechanic`) used to route user decisions.