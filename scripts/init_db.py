import sqlite3
import os


def init_db():
    # Ensure the uploads directory exists for images
    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    conn = sqlite3.connect("/app/manul_leads.db")
    cursor = conn.cursor()

    # 1. Users Table (Authorization)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            role TEXT DEFAULT 'staff',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Leads Table (For Facebook Scraping results)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            post_content TEXT, 
            post_url TEXT UNIQUE, 
            status TEXT DEFAULT 'new',
            assigned_to INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(assigned_to) REFERENCES users(user_id)
        )
    """)

    # 3. Seen Leads Table (To prevent duplicate AI analysis in Hunter)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seen_leads (
            url TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 4. Marketing Posts Table (For Vision results)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS marketing_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            image_path TEXT,
            generated_content TEXT,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database defined and tables created successfully.")


if __name__ == "__main__":
    init_db()
