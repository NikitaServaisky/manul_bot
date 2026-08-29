import os
from src.database.connection import get_db

def seed_admin_user():
    """Checks if the bootstrap Admin exists in the database. If not, creates them."""
    admin_id_str = os.getenv("TELEGRAM_CHAT_ID")
    if not admin_id_str:
        print("⚠️ TELEGRAM_CHAT_ID not found in .env, skipping admin seeding.")
        return

    admin_tg_id = int(admin_id_str)

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT user_id FROM users WHERE user_id = %s;", (admin_tg_id,))
                admin_user = cur.fetchone()

                if not admin_user:
                    print(f"🚀 Seeding Admin user (ID: {admin_tg_id}) into PostgreSQL...")
                    
                    cur.execute("""
                        INSERT INTO users (user_id, username, role, is_active)
                        VALUES (%s, %s, %s, %s);
                    """, (admin_tg_id, "admin", "owner", 1))
                    
                    conn.commit()
                    print("✅ Admin user seeded successfully.")
                else:
                    print("ℹ️ Admin user already exists in the database.")
                    
    except Exception as e:
        print(f"❌ Error during admin seeding: {e}")

if __name__ == "__main__":
    seed_admin_user()