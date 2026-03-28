from core.database import get_db_connection

def is_user_authorized(user_id):
    """Check if a user is active in the system"""
    try:
        with get_db() as conn:
            res = conn.execute(
                "SELECT is_active FROM users WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            return res is not None and res['is_active'] == 1
    except Exception as e:
        logging.error(f"Auth Error: {e}")
        return False