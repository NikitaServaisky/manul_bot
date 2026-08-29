import logging
from src.database.user_repository import get_db
from src.database.get_schema_files import get_schema_files

# Setup logger for this file
logger = logging.getLogger(__name__)


def apply_schema():
    """
    Scans and executes all SQL schema files found in the schema directory.
    Ensures the database structure is up to date.
    """
    schema_files = get_schema_files()

    if not schema_files:
        logger.warning("No schema files found to apply.")
        return

    try:
        # Establish a single connection for the entire process
        with get_db() as conn:
            with conn.cursor() as cur:
                for file_path in schema_files:
                    logger.info(f"Applying schema: {file_path}...")
                    
                    with open(file_path, "r", encoding="utf-8") as f:
                        sql = f.read()
                        
                        # Execute only if the file is not empty
                        if sql.strip():
                            cur.execute(sql)
                
                # Commit all changes at once for atomicity
                conn.commit()
                logger.info("✅ All schemas applied successfully.")
                
    except Exception as e:
        logger.exception(f"❌ Error applying schema: {e}")
        # In a 'with' block, the connection will close, 
        # but we raise the error to alert the system.
        raise