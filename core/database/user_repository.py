import logging
from core.database import get_db
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

def db_get_user_by_id(user_id):
    """ Fetches a raw user row from the database by user_id."""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                return cur.fetchone()
    except Exception as e:
        logger.exception(f"DB Error fetching user {user_id}: {e}")
        return None

def db_save_user(user_id, username, role, data_dict):
    """ Executes the INSERT/UPDATE query using raw dictionary values."""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
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
                        bank_account_number = EXCLUDED.bank_account_number,
                        is_active = 1;
                    """,
                    (
                        user_id, username, role, 
                        data_dict.get("id_number"), data_dict.get("phone_number"), 
                        data_dict.get("salary_type"), data_dict.get("base_salary_rate"), 
                        data_dict.get("bank_name"), data_dict.get("bank_branch"), 
                        data_dict.get("bank_account_number")
                    ),
                )
            conn.commit()
            return True
    except Exception as e:
        logger.exception(f"DB Error saving user {username}: {e}")
        raise