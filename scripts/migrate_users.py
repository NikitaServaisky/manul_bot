import sqlite3
import logging
from core.database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_users(sqlite_db_path="data/manul_leads.db"):
    """
    Migrates users from the old SQLite database to the new PostgreSQL server.
    """
    try:
        # Connect to the old SQLite database
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cur = sqlite_conn.cursor()

        # Fetch all users from SQLite
        sqlite_cur.execute("SELECT user_id, username, role, is_active FROM users")
        users = sqlite_cur.fetchall()

        if not users:
            logger.info("No users found in the old SQLite database.")
            return

        # Connect to the new PostgreSQL database
        with get_db() as pg_conn:
            with pg_conn.cursor() as pg_cur:
                for user in users:
                    logger.info(
                        f"Migrating user: {user['username']} (ID: {user['user_id']})"
                    )

                    # Insert or update user in PostgreSQL
                    pg_cur.execute(
                        """
                        INSERT INTO users (user_id, username, role, is_active)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (user_id) DO UPDATE SET
                            username = EXCLUDED.username,
                            role = EXCLUDED.role,
                            is_active = EXCLUDED.is_active;
                    """,
                        (
                            user["user_id"],
                            user["username"],
                            user["role"],
                            user["is_active"],
                        ),
                    )

                pg_conn.commit()

        logger.info(f"✅ Successfully migrated {len(users)} users to PostgreSQL.")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
    finally:
        if sqlite_conn:
            sqlite_conn.close()


if __name__ == "__main__":
    migrate_users()
