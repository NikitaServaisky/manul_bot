import os
import logging
from src.database.user_repository import get_db
from src.database.get_schema_files import get_schema_files

# Logger setup for this file
logger = logging.getLogger(__name__)


def init_db():
    """
    Database Initialization Engine:
    1. Creates the necessary directory structure.
    2. Scans SQL files from the schema directory.
    3. Executes them sequentially on the PostgreSQL database.
    """
    
    # Base directories for the project
    base_dirs = [
        "data",
        "uploads/marketing",
        "uploads/employees", # Base directory for all employee documents
        "uploads/temp"       # Temporary directory for processing uploads
    ]

    # Explicitly define the execution order to prevent alphabetical sorting bugs
    SCHEMA_FILES = [
        "1_1_users.sql",
        "1_2_expend_users_table.sql",
        "1_3users_documents.sql",
        "02_leads.sql",
        "03_inventory.sql",
        "04_costumers_and_vehicles.sql",
        "05_vacation_requests.sql",
        "06_shift_submissions.sql",
        "07_work_schedule.sql"
    ]

    for directory in base_dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"📁 Created '{directory}' directory.")


    if not SCHEMA_FILES:
        logger.warning("⚠️ No SQL schema files defined in SCHEMA_FILES.")
        return

    try:
        # Establish connection to PostgreSQL
        with get_db() as conn:
            with conn.cursor() as cur:
                
                for file_name in SCHEMA_FILES:
                    # English comment: Construct the full path to the schema file
                    file_path = os.path.join("schema", file_name)
                    
                    logger.info(f"📜 Executing schema: {file_path}")

                    with open(file_path, "r", encoding="utf-8") as f:
                        sql_script = f.read()

                        if sql_script.strip():
                            cur.execute(sql_script)

                # Commit all changes to the database
                conn.commit()

        logger.info("✅ Database initialized and schemas applied successfully.")

    except Exception as e:
        logger.exception(f"❌ Failed to initialize database: {e}")

def prepare_employee_directory(user_id):
    """
    Creates a dedicated folder for a specific employee if it doesn't exist.
    This should be called during the 'Add Employee' flow or when uploading a doc.
    """
    path = f"uploads/employees/{user_id}/documents"
    if not os.path.exists(path):
        os.makedirs(path)
        logger.info(f"📁 Created private directory for employee: {user_id}")
    return path


if __name__ == "__main__":
    init_db()