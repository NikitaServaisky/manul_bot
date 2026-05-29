import logging
from core.security import encrypt_data, decrypt_data
from core.database.user_repository import db_get_user_by_id, db_save_user

logger = logging.getLogger(__name__)

# List of fields that require encryption/decryption
SENSITIVE_FIELDS = [
    "id_number", "phone_number", "salary_type", 
    "base_salary_rate", "bank_name", "bank_branch", "bank_account_num"
]

def _encrypt_payload(kwargs):
    """ Helper to encrypt sensitive fields before passing to repository."""
    encrypted_payload = {}
    for field in SENSITIVE_FIELDS:
        raw_val = kwargs.get(field)
        encrypted_payload[field] = encrypt_data(str(raw_val)) if raw_val is not None else None
    return encrypted_payload

def _decrypt_payload(user_dict):
    """ Helper to decrypt sensitive fields received from repository."""
    if not user_dict:
        return user_dict
    for field in SENSITIVE_FIELDS:
        if user_dict.get(field):
            user_dict[field] = decrypt_data(user_dict[field])
    return user_dict


def is_user_authorized(user_id):
    """Checks if the user is authorized and active in the system."""
    user = db_get_user_by_id(user_id)
    return user is not None and user.get("is_active") == 1


def get_user_role(user_id):
    """Retrieves the user's role."""
    user = db_get_user_by_id(user_id)
    return user.get("role") if user and user.get("is_active") == 1 else None


def add_user(user_id, username, role="staff", **kwargs):
    """Registers or updates a user. Handles encryption automatically."""
    encrypted_data = _encrypt_payload(kwargs)
    # Pass clean, encrypted data directly to the repository layer
    db_save_user(user_id, username, role, encrypted_data)
    logger.info(f"✅ User {username} processed and saved securely via Service Layer.")


def get_employee_card(user_id):
    """Retrieves full details and decrypts sensitive fields for display."""
    raw_user = db_get_user_by_id(user_id)
    return _decrypt_payload(raw_user)