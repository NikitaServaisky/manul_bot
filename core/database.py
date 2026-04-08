import sqlite3


def get_db():
    """connect to data base function"""
    db_path = "/app/manul_leads.db"
    conn = sqlite3.connect("manul_leads.db")
    conn.row_factory = sqlite3.Row
    return conn
