from datetime import date
from src.database.user_repository import get_db

def fetch_employee_schedule(user_id: int, start_date: date, end_date: date):
    """
    Fetches published shifts for a user between specific dates.
    """
    query = """
        SELECT shift_date, start_time, end_time, assigned_role, notes
        FROM work_schedule
        WHERE user_id = %s 
          AND shift_date BETWEEN %s AND %s
          AND is_published = TRUE
        ORDER BY shift_date ASC;
    """
    with get_db() as conn:
        # Using RealDictCursor for cleaner dictionary results if desired, or standard cursor
        with conn.cursor() as cursor:
            cursor.execute(query, (user_id, start_date, end_date))
            return cursor.fetchall()

from src.database.user_repository import get_db

def create_vacation_request(user_id: int, req_type: str, start_date, end_date, total_days: float) -> int:
    """Inserts a vacation request into PostgreSQL and returns the generated request ID."""
    query = """
        INSERT INTO vacation_requests (user_id, request_type, start_date, end_date, total_days, status)
        VALUES (%s, %s, %s, %s, %s, 'Pending')
        RETURNING user_id;
    """
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (user_id, req_type, start_date, end_date, total_days))
                result = cur.fetchone()
                conn.commit()
                return result[0] if result else 0
    except Exception as e:
        print(f"Error creating vacation request: {e}")
        return 0

def update_vacation_status(request_id: int, status: str):
    """Updates the status of a specific vacation request (Approved / Rejected)."""
    query = "UPDATE vacation_requests SET status = %s WHERE id = %s RETURNING user_id, start_date, end_date;"
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (status, request_id))
                result = cur.fetchone()
                conn.commit()
                return result # Returns (user_id, start_date, end_date)
    except Exception as e:
        print(f"Error updating vacation status: {e}")
        return None

def log_user_document(user_id: int, doc_type: str, path: str, name: str, size: int):
    """
    Saves metadata of an uploaded file into user_documents.
    """
    query = """
        INSERT INTO user_documents (user_id, doc_type, file_path, file_name, file_size_kb)
        VALUES (%s, %s, %s, %s, %s) RETURNING id;
    """
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (user_id, doc_type, path, name, size))
            doc_id = cursor.fetchone()[0]
            conn.commit()
            return doc_id

def save_shift_submission(user_id: int, shift_date: date, preference: str, notes: str = None):
    """
    Inserts or update an employee's availability for a spesific date.
    """
    query = """
        INSERT INTO shift_submissions (user_id, shift_date, preference, user_note)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id, shift_date)
        DO UPDATE SET preference = EXCLUDED.preference, user_note = EXCLUDED.user_note;
    """
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (user_id, shift_date, preference, notes))
            conn.commit()
