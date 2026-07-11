import os
import logging
from core.security import encrypt_data, decrypt_data
from core.database.user_repository import db_get_user_by_id, db_save_user
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

SENSITIVE_FIELDS = [
    "id_number", "phone_number", "salary_type", 
    "base_salary_rate", "bank_name", "bank_branch", "bank_account_number"
]

load_dotenv()

def _encrypt_payload(kwargs):
    encrypted_payload = {}
    for field in SENSITIVE_FIELDS:
        raw_val = kwargs.get(field)
        encrypted_payload[field] = encrypt_data(str(raw_val)) if raw_val is not None else None
    return encrypted_payload

def _decrypt_payload(user_dict):
    if not user_dict:
        return user_dict
    for field in SENSITIVE_FIELDS:
        if user_dict.get(field):
            user_dict[field] = decrypt_data(user_dict[field])
    return user_dict

def is_user_authorized(user_id):
    user = db_get_user_by_id(user_id)
    # FIXED: Safe truthy check for active state
    return user is not None and bool(user.get("is_active"))

def is_user_admin(user_id):
    ADMIN_ID = int(os.getenv("TELEGRAM_CHAT_ID", 0))
    if user_id == ADMIN_ID:
        return True
        
    user = db_get_user_by_id(user_id)
    return user is not None and bool(user.get("is_active")) and user.get("role") == "owner"

def get_user_role(user_id):
    """Retrieves the user's role safely."""
    user = db_get_user_by_id(user_id)
    return user.get("role") if user and bool(user.get("is_active")) else None

def add_user(user_id, username, role="staff", **kwargs):
    encrypted_data = _encrypt_payload(kwargs)
    db_save_user(user_id, username, role, encrypted_data)
    logger.info(f"✅ User {username} processed and saved securely via Service Layer.")

def get_employee_card(user_id):
    raw_user = db_get_user_by_id(user_id)
    return _decrypt_payload(raw_user)