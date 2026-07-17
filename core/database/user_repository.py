import logging
import psycopg2
from core.database import get_db
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

def db_get_user_by_db_id(db_id: int):
    """Fetches a raw user row from the database by the internal serial primary key ID."""
    if not db_id:
        return None
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE id = %s", (db_id,))
                return cur.fetchone()
    except Exception as e:
        logger.exception(f"DB Error fetching user by internal ID {db_id}: {e}")
        return None

def db_get_user_by_id(user_id: int):
    """Fetches a raw user row from the database by telegram user_id."""
    if not user_id:
        return None
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                return cur.fetchone()
    except Exception as e:
        logger.exception(f"DB Error fetching user {user_id}: {e}")
        return None

def db_get_all_users():
    """Fetches all users from the database for global operations and scanning."""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM users")
                return cur.fetchall()
    except Exception as e:
        logger.exception(f"DB Error fetching all users: {e}")
        return []

def db_save_user(db_id: int, user_id: int, username: str, role: str, encrypted_data: dict) -> int:
    """
    Saves or updates a complete user record safely using the internal database ID 
    to prevent identity duplication and unique key constraint issues.
    """
    encrypted_phone = encrypted_data.get("phone_number")
    
    # Path 1: Targeted update when the explicit serial primary key is provided
    if db_id:
        query = """
            UPDATE users SET
                user_id = COALESCE(%s, user_id),
                username = %s,
                role = %s,
                id_number = %s,
                phone_number = %s,
                salary_type = %s,
                base_salary_rate = %s,
                bank_name = %s,
                bank_branch = %s,
                bank_account_number = %s,
                is_active = 1
            WHERE id = %s
            RETURNING id;
        """
        params = (
            user_id, username, role, encrypted_data.get("id_number"), encrypted_phone,
            encrypted_data.get("salary_type"), encrypted_data.get("base_salary_rate"),
            encrypted_data.get("bank_name"), encrypted_data.get("bank_branch"), encrypted_data.get("bank_account_number"),
            db_id
        )
    # Path 2: Upsert based on existing Telegram user_id to avoid unique violations on re-registration
    elif user_id:
        query = """
            INSERT INTO users (
                user_id, username, role, id_number, phone_number, 
                salary_type, base_salary_rate, bank_name, bank_branch, bank_account_number, is_active
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                username = EXCLUDED.username,
                role = EXCLUDED.role,
                id_number = EXCLUDED.id_number,
                phone_number = COALESCE(EXCLUDED.phone_number, users.phone_number),
                salary_type = EXCLUDED.salary_type,
                base_salary_rate = EXCLUDED.base_salary_rate,
                bank_name = EXCLUDED.bank_name,
                bank_branch = EXCLUDED.bank_branch,
                bank_account_number = EXCLUDED.bank_account_number,
                is_active = 1
            RETURNING id;
        """
        params = (
            user_id, username, role, encrypted_data.get("id_number"), encrypted_phone,
            encrypted_data.get("salary_type"), encrypted_data.get("base_salary_rate"),
            encrypted_data.get("bank_name"), encrypted_data.get("bank_branch"), encrypted_data.get("bank_account_number"),
            1
        )
    # Path 3: Pre-registration path where user_id is missing/NULL; conflicts fall back on phone numbers
    else:
        query = """
            INSERT INTO users (
                user_id, username, role, id_number, phone_number, 
                salary_type, base_salary_rate, bank_name, bank_branch, bank_account_number, is_active
            )
            VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (phone_number) DO UPDATE SET
                username = EXCLUDED.username,
                role = EXCLUDED.role,
                id_number = EXCLUDED.id_number,
                salary_type = EXCLUDED.salary_type,
                base_salary_rate = EXCLUDED.base_salary_rate,
                bank_name = EXCLUDED.bank_name,
                bank_branch = EXCLUDED.bank_branch,
                bank_account_number = EXCLUDED.bank_account_number,
                is_active = 1
            RETURNING id;
        """
        params = (
            username, role, encrypted_data.get("id_number"), encrypted_phone,
            encrypted_data.get("salary_type"), encrypted_data.get("base_salary_rate"),
            encrypted_data.get("bank_name"), encrypted_data.get("bank_branch"), encrypted_data.get("bank_account_number"),
            1
        )
    
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone()
                if result:
                    conn.commit()
                    return result[0]
                return 0
    except psycopg2.errors.UniqueViolation:
        logger.warning("Data collision detected. Unique constraint violated on phone or telegram user_id.")
        return 0
    except Exception as e:
        logger.exception(f"DB Error saving user record: {e}")
        return 0

def db_get_pending_users():
    """Fetches only pre-registered users who haven't linked a Telegram ID yet to prevent spoofing/hijacking."""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE user_id IS NULL")
                return cur.fetchall()
    except Exception as e:
        logger.exception(f"DB Error fetching pending users: {e}")
        return []

def db_link_telegram_to_user(encrypted_phone: str, telegram_id: int, username: str) -> bool:
    """
    Links a Telegram account infrastructure profile to an existing pre-registered record via encrypted phone.
    Returns True only if a row was actually updated. Safe against profile hijacking.
    """
    query = """
        UPDATE users 
        SET user_id = %s, username = %s, is_active = 1
        WHERE phone_number = %s AND user_id IS NULL;
    """
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (telegram_id, username, encrypted_phone))
                if cursor.rowcount > 0:
                    conn.commit()
                    return True
                else:
                    logger.warning("No pending user found with the provided phone number or user_id is already linked.")
                    return False
    except Exception as e:
        logger.exception(f"DB Error linking telegram ID to encrypted phone instance: {e}")
        return False