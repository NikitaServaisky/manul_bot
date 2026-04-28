import psycopg2
from psycopg2.extras import RealDictCursor
import os
from contextlib import contextmanager


@contextmanager
def get_db():
    """
    Establishes a connection to the PostgreSQL database.
    Uses environment variables for configuration.
    The context manager ensures the connection is closed automatically.
    """
    conn = None
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "db"),
            database=os.getenv("DB_NAME", "manul_leads"),
            user=os.getenv("DB_USER", "admin"),  # Fixed typo: BD_USER -> DB_USER
            password=os.getenv("DB_PASSWORD", "pass"),
            port=os.getenv("DB_PORT", "5432"),  # Changed default to standard port 5432
        )
        yield conn
    except Exception as e:
        # If there's a connection error, it will be caught here
        print(f"Database connection error: {e}")
        raise
    finally:
        # Ensures the connection is closed after use
        if conn:
            conn.close()
