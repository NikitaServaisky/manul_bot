import logging
from core.database import get_db
from psycopg2.extras import RealDictCursor

# Basic logging configuration
logger = logging.getLogger(__name__)

def is_user_authorized(user_id):
    """Checks if the user is authorized and active in the system."""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Removed the trailing comma from cur.execute
                cur.execute("SELECT is_active FROM users WHERE user_id = %s", (user_id,))
                response = cur.fetchone()

            # Check if user exists and is active
            return response is not None and response["is_active"] == 1
    except Exception as e:
        logger.error(f"Auth Error: {e}")
        return False


def add_user(user_id, username, role="staff"):
    """Registers a new user into the database with a specific role."""
    try:
        with get_db() as conn:
            # Using PostgreSQL ON CONFLICT syntax instead of SQLite syntax
            with conn.cursor() as cur:
                cur.execute(
                    """
                        INSERT INTO users (user_id, username, role, is_active) 
                        VALUES (%s, %s, %s, 1)
                        ON CONFLICT (user_id) DO UPDATE SET
                            username = EXCLUDED.username,
                            role = EXCLUDED.role,
                            is_active = 1;
                        """,
                    (user_id, username, role),
                )
            conn.commit()
            print(f"✅ User {username} ({role}) added successfully.")
    except Exception as e:
        logger.error(f"Failed to add user: {e}")
        raise


def get_user_role(user_id):
    """Retrieves the user's role from the database."""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT role FROM users WHERE user_id = %s AND is_active = 1",
                    (user_id,)
                )
                response = cur.fetchone()
                return response["role"] if response else None
    except Exception as e:
        logger.error(f"Error fetching role: {e}")
        return None
