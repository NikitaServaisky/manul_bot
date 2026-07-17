import logging
from core.database import get_db
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

def db_get_user_by_id(user_id):
    """Fetches a raw user row from the database by user_id."""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                return cur.fetchone()
    except Exception as e:
        logger.exception(f"DB Error fetching user {user_id}: {e}")
        return None

def db_save_user(user_id: int, username: str, role: str, encrypted_data: dict):
    """Saves or updates a complete user record dynamically based on existence of user_id."""
    encrypted_phone = encrypted_data.get("phone_number")
    
    # If no telegram user_id is provided yet (pre-registration case)
    if not user_id:
        # Avoid explicit NULL injection into uniqueness-constrained fields if architectural limits exist
        query = """
            INSERT INTO users (
                username, role, id_number, phone_number, 
                salary_type, base_salary_rate, bank_name, bank_branch, bank_account_number, is_active
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
            ON CONFLICT (phone_number) DO UPDATE SET
                username = EXCLUDED.username,
                role = EXCLUDED.role,
                id_number = EXCLUDED.id_number,
                salary_type = EXCLUDED.salary_type,
                base_salary_rate = EXCLUDED.base_salary_rate,
                bank_name = EXCLUDED.bank_name,
                bank_branch = EXCLUDED.bank_branch,
                bank_account_number = EXCLUDED.bank_account_number;
        """
        params = (
            username, role, encrypted_data.get("id_number"), encrypted_phone,
            encrypted_data.get("salary_type"), encrypted_data.get("base_salary_rate"),
            encrypted_data.get("bank_name"), encrypted_data.get("bank_branch"), encrypted_data.get("bank_account_number")
        )
    else:
        # Standard conflict resolution using primary telegram user_id key or matching phone constraints
        query = """
            INSERT INTO users (
                user_id, username, role, id_number, phone_number, 
                salary_type, base_salary_rate, bank_name, bank_branch, bank_account_number, is_active
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
            ON CONFLICT (user_id) DO UPDATE SET
                username = EXCLUDED.username,
                role = EXCLUDED.role,
                id_number = EXCLUDED.id_number,
                phone_number = EXCLUDED.phone_number,
                salary_type = EXCLUDED.salary_type,
                base_salary_rate = EXCLUDED.base_salary_rate,
                bank_name = EXCLUDED.bank_name,
                bank_branch = EXCLUDED.bank_branch,
                bank_account_number = EXCLUDED.bank_account_number;
        """
        params = (
            user_id, username, role, encrypted_data.get("id_number"), encrypted_phone,
            encrypted_data.get("salary_type"), encrypted_data.get("base_salary_rate"),
            encrypted_data.get("bank_name"), encrypted_data.get("bank_branch"), encrypted_data.get("bank_account_number")
        )
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            conn.commit()

def db_get_all_users():
    """Fetches all users from the database for phone verification scanning."""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM users")
                return cur.fetchall()
    except Exception as e:
        logger.exception(f"DB Error fetching all users: {e}")
        return []

def db_link_telegram_to_user(encrypted_phone: str, telegram_id: int, username: str):
    """Links a Telegram account infrastructure profile to an existing pre-registered record via encrypted phone."""
    query = """
        UPDATE users 
        SET user_id = %s, username = %s, is_active = 1
        WHERE phone_number = %s;
    """
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (telegram_id, username, encrypted_phone))
                conn.commit()
                return True
    except Exception as e:
        logger.exception(f"DB Error linking telegram ID to encrypted phone instance: {e}")
        return False