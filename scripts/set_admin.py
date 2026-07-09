import os

# Using the exact same module paths your main app uses
from database import SessionLocal  # If this fails, change to: from core.database.config import SessionLocal (or wherever init_db gets it)
from models import User            # Using the absolute layout from the root


def seed_admin_user():
    """Checks if the bootstrap Admin exists in the database. If not, creates them."""
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
            print(f"🚀 Seeding Admin user (ID: {admin_tg_id}) into the database...")
            new_admin = User(
                telegram_id=admin_tg_id,
                name="System Admin",
                role="owner",  # Setting your role as Owner
            )
            session.add(new_admin)
            session.commit()
            print("✅ Admin user seeded successfully.")
        else:
            print("ℹ️ Admin user already exists in the database.")
    except Exception as e:
        session.rollback()
        print(f"❌ Error during admin seeding: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    seed_admin_user()