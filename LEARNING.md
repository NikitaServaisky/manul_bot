# 📘 Learning & Variables Dictionary

## Application States (ConversationHandlers)
- `ADDING_USER_FLOW`: Handles the step-by-step process of adding a new employee via contact selection.
- `WAITING_FOR_POST_IMAGE`: State where the bot waits for the mechanic to send a photo or text for AI analysis.
- `EDITING_TEXT`: State where the bot waits for the user to provide manual corrections to the AI-generated post.

## Key Variables
- `ADMIN_ID`: The Telegram Chat ID of Nikita (Super-user). Fetched from `.env`.
- `target_id`: Used during the registration flow to store the ID of the person being added.
- `role`: Defines access levels: `mechanic` (posts only), `owner` (posts + user management).

## Functional Components
- `request_users`: A Telegram API feature (v6.7+) that opens the user picker instead of manual ID entry.
- `callback_data`: String labels (e.g., `setrole_123_mechanic`) passed when clicking Inline Buttons to trigger specific logic.