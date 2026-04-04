import logging
from core.database import get_db

# Basic logging configuration
logging.basicConfig(level=logging.INFO)


def is_user_authorized(user_id):
    """Checks if the user is authorized and active in the system."""
    try:
        with get_db() as conn:
            # Using 'response' as requested
            response = conn.execute(
                "SELECT is_active FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()

            # Check if user exists and is active
            return response is not None and response["is_active"] == 1
    except Exception as e:
        logging.error(f"Auth Error: {e}")
        return False


def add_user(user_id, username, role="staff"):
    """Registers a new user into the database with a specific role."""
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO users (user_id, username, role, is_active) VALUES (?, ?, ?, ?)",
                (user_id, username, role, 1),
            )
            conn.commit()
            print(f"✅ User {username} ({role}) added successfully.")
    except Exception as e:
        logging.error(f"Failed to add user: {e}")


def get_user_role(user_id):
    """Retrieves the user's role from the database."""
    try:
        with get_db() as conn:
            response = conn.execute(
                "SELECT role FROM users WHERE user_id = ? AND is_active = 1", (user_id,)
            ).fetchone()
            return response["role"] if response else None
    except Exception as e:
        logging.error(f"Error fetching role: {e}")
        return None
