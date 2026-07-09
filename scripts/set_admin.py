import os
from database import SessionLocal
from models import User


def seed_admin_user():
    """Checks if the bootstrap Admin exists in the database. If not' creates them."""
    admin_id_str = os.getenv("TELEGRAM_CHAT_ID")
    if not admin_id_str:
        print("⚠️ TELEGRAM_CHAT_ID not found in .env, skipping admin seeding.")
        return

    admin_tg_id = int(admin_id_str)
    session = SessionLocal()

    try:
        # Check if this Telegram ID already exists in the users table
        admin_user = session.query(User).filter(User.telegram_id == admin_tg_id).first()

        if not admin_user:
            print(f"🚀 seeding Admin user (ID: {admin_tg_id}) into the database...")
            new_admin = User(
                telegram_id=admin_tg_id,
                name="System Admin",
                role="owner",  # Setting your role as Owner
            )
            sessino.add(new_admin)
            session.commit()
            print("✅ Admin user seeded successfully.")
        else:
            print("ℹ️ Admin user already exists in the database.")
    except Exception as e:
        session.rollback()
        print(f"❌ Error during admin seeding: {e}")
    finally:
        session.close()


# Call this function inside your main.py startup workflow
if __name__ == "__main__":
    seed_admin_user()
    # ... rest of your bot startup logic (e.g., application.run_polling())
