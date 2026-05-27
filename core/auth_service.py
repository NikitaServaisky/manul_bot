import logging
from core.database import get_db
from psycopg2.extras import RealDictCursor
from core.security import encrypt_data, decrypt_data # Importing the helpers we discussed

# Basic logging configuration
logger = logging.getLogger(__name__)

def is_user_authorized(user_id):
    """Checks if the user is authorized and active in the system."""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT is_active FROM users WHERE user_id = %s", (user_id,)
                )
                response = cur.fetchone()
            return response is not None and response["is_active"] == 1
    except Exception as e:
        logger.exception(f"Auth Error: {e}")
        return False

def add_user(user_id, username, role="staff", **kwargs):
    """
    Registers or updates a user. 
    Sensitive data (id_number) is encrypted before saving.
    """
    try:
        # 1. Encrypt sensitive fields
        raw_id_number = kwargs.get("id_number")
        encrypted_id = encrypt_data(raw_id_number) if raw_id_number else None
        
        phone_number = kwargs.get("phone_number")
        salary_type = kwargs.get("salary_type", "hourly")
        base_salary_rate = kwargs.get("base_salary_rate", 0.0)

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (
                        user_id, username, role, id_number, 
                        phone_number, salary_type, base_salary_rate, is_active
                    ) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
                    ON CONFLICT (user_id) DO UPDATE SET
                        username = EXCLUDED.username,
                        role = EXCLUDED.role,
                        id_number = EXCLUDED.id_number,
                        phone_number = EXCLUDED.phone_number,
                        salary_type = EXCLUDED.salary_type,
                        base_salary_rate = EXCLUDED.base_salary_rate,
                        is_active = 1;
                    """,
                    (
                        user_id, username, role, encrypted_id, 
                        phone_number, salary_type, base_salary_rate
                    ),
                )
            conn.commit()
            logger.info(f"✅ User {username} saved with encrypted sensitive data.")
    except Exception as e:
        logger.exception(f"Failed to add user: {e}")
        raise

def get_employee_card(user_id):
    """
    Retrieves full details and decrypts sensitive fields for display.
    """
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                user = cur.fetchone()
        
        if user and user.get("id_number"):
            # 2. Decrypt for the UI
            user["id_number"] = decrypt_data(user["id_number"])
            
        return user
    except Exception as e:
        logger.exception(f"Error fetching employee card: {e}")
        return None

def get_user_role(user_id):
    """Retrieves the user's role."""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT role FROM users WHERE user_id = %s AND is_active = 1",
                    (user_id,),
                )
                response = cur.fetchone()
                return response["role"] if response else None
    except Exception as e:
        logger.exception(f"Error fetching role: {e}")
        return None