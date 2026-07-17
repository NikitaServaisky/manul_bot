import os
import logging
from core.security import encrypt_data, decrypt_data
from core.database.user_repository import (
    db_get_user_by_id, 
    db_save_user, 
    db_get_pending_users, 
    db_link_telegram_to_user
)
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

def _normalize_phone(raw_phone: str) -> str:
    """Standardizes phone numbers by extracting digits and normalizing country codes."""
    if not raw_phone:
        return ""
    digits = "".join(filter(str.isdigit, str(raw_phone)))
    if digits.startswith("05") and len(digits) == 10:
        digits = "972" + digits[1:]
    return digits

def is_user_authorized(user_id):
    if not user_id:
        return False
    user = db_get_user_by_id(user_id)
    return user is not None and bool(user.get("is_active"))

def is_user_admin(user_id):
    if not user_id:
        return False
    ADMIN_ID = int(os.getenv("TELEGRAM_CHAT_ID", 0))
    if user_id == ADMIN_ID:
        return True
        
    user = db_get_user_by_id(user_id)
    return user is not None and bool(user.get("is_active")) and user.get("role") == "owner"

def get_user_role(user_id):
    """Retrieves the user's role safely."""
    if not user_id:
        return None
    user = db_get_user_by_id(user_id)
    return user.get("role") if user and bool(user.get("is_active")) else None

def add_user(user_id: int, username: str, role="staff", db_id: int = None, **kwargs) -> int:
    """
    Processes encryption and routes data to user_repository safely.
    Explicitly maps named arguments to prevent runtime alignment signature mismatches.
    """
    encrypted_data = _encrypt_payload(kwargs)
    
    # Correctly routes explicit arguments to match updated repository signature
    saved_db_id = db_save_user(
        db_id=db_id, 
        user_id=user_id, 
        username=username, 
        role=role, 
        encrypted_data=encrypted_data
    )
    
    if saved_db_id > 0:
        logger.info(f"✅ User {username} processed and saved securely via Service Layer. Internal ID: {saved_db_id}")
    else:
        logger.error(f"❌ Failed to process or save user {username} due to constraints violation or signature mismatch.")
        
    return saved_db_id

def get_employee_card(user_id):
    if not user_id:
        return None
    raw_user = db_get_user_by_id(user_id)
    return _decrypt_payload(raw_user)

def authorize_user_by_phone(telegram_id, username, raw_phone_number):
    """
    Iterates through unlinked pending database users, decrypts their phone numbers,
    and checks for an exact normalized match to prevent account hijacking or country code spoofing.
    """
    pending_users = db_get_pending_users()
    if not pending_users:
        logger.warning("No unlinked pending users found in database during phone authorization verification.")
        return False

    incoming_phone = _normalize_phone(raw_phone_number)
    if not incoming_phone:
        return False

    for user in pending_users:
        encrypted_phone = user.get("phone_number")
        if encrypted_phone:
            try:
                decrypted_phone = decrypt_data(encrypted_phone)
                cleaned_stored_phone = _normalize_phone(decrypted_phone)

                if cleaned_stored_phone and incoming_phone == cleaned_stored_phone:
                    logger.info(f"🎯 Exact match found for pending user profile. Linking Telegram ID {telegram_id} to record.")
                    
                    resolved_username = username or user.get("username") or f"user_{telegram_id}"
                    
                    return db_link_telegram_to_user(
                        encrypted_phone=encrypted_phone,
                        telegram_id=telegram_id,
                        username=resolved_username
                    )
            except Exception as e:
                logger.error(f"Failed to decrypt or process phone verification loop step: {e}")
                continue
    return False