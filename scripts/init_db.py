import os
import logging
from core.database import get_db
from core.setup.get_schema_files import get_schema_files

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db():
    """
    Database Initialization Engine:
    1. Creates the uploads directory if it doesn't exist.
    2. Scans SQL files from the schema directory.
    3. Executes them sequentially on the PostgreSQL database.
    """
    # Updated part for init_db.py


if not os.path.exists("uploads/marketing"):
    os.makedirs("uploads/marketing")
    logger.info("📁 Created 'uploads/marketing' directory for AI analysis.")

    # Create the data directory for migration files and exports
    if not os.path.exists("data"):
        os.makedirs("data")
        logger.info("📁 Created 'data' directory.")

    # Get the sorted list of schema files (01, 02, 03...)
    schema_files = get_schema_files()

    if not schema_files:
        logger.warning("⚠️ No SQL schema files found in the schema/ directory.")
        return

    try:
        # Establish connection to PostgreSQL
        with get_db() as conn:
            with conn.cursor() as cur:
                for file_path in schema_files:
                    logger.info(f"📜 Executing schema: {file_path}")

                    with open(file_path, "r", encoding="utf-8") as f:
                        sql_script = f.read()

                        if sql_script.strip():
                            cur.execute(sql_script)

                # Commit all changes to the database
                conn.commit()

        logger.info("✅ Database initialized and schemas applied successfully.")

    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")

if __name__ == "__main__":
    init_db()
