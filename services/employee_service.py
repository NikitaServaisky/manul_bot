from datetime import date
from core.database import get_db

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

def create_vacation_request(user_id: int, req_type: str, start: date, end: date, days: float, notes: str = None):
    """
    Inserts a new leave request (vacation/sick).
    """
    query = """
        INSERT INTO vacation_requests (user_id, request_type, start_date, end_date, total_days, user_notes)
        VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;
    """
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (user_id, req_type, start, end, days, notes))
            req_id = cursor.fetchone()[0]
            conn.commit()
            return req_id

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