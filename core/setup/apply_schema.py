from core.database import get_db
from core.setup.get_schema_files import get_schema_files


def apply_schema():
    """Runing all files of schema has found in database"""
    schema_files = get_schema_files()

    if not schema_files:
        print(f"No schema files to apply")
        return

    try:
        # run one connettion for one process
        with conn.cursor() as cur:
            for file_path in schema_files:
                print(f"Applying {file_path}...")
                with open(file_path, "r", encoding="utf-8") as f:
                    sql = f.read()
                    if sql.strip():
                        cur.execute(sql)

            # neccesery get commit for save
            conn.commit()
    except Exception as e:
        print(f"Error applying schema: {e}")
