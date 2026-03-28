import sqlite3

def get_db():
    """connect to data base function"""
    conn = sqlite3.connect("manul_leads.db")
    conn.row_factory = sqlite3.Row
    return conn