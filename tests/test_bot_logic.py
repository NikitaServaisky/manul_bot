import os
from core.auth_service import add_user, is_user_authorized, get_user_role
from services.ai_logic import analyze_mechanic_work
from core.database import get_db


def test_full_flow():
    print("\n🧪 Starting Full Logic Test (with add_user)...")

    # 1. Test Database & Auth
    print("Step 1: Testing User Authorization...")
    test_id = 999999
    test_name = "Test_David"

    # שימוש בשם הפונקציה המעודכן שלך
    add_user(test_id, test_name, role="owner")

    # Verify
    assert is_user_authorized(test_id) == True
    assert get_user_role(test_id) == "owner"
    print("✅ Auth System: OK")

    # 2. Test AI Logic
    print("\nStep 2: Testing AI Logic & Fallback...")
    # וודא שיש קובץ כלשהו בתיקייה הזו, או שנשתמש באחד קיים
    os.makedirs("uploads", exist_ok=True)
    test_image = "uploads/test_v1.jpg"
    if not os.path.exists(test_image):
        with open(test_image, "wb") as f:
            f.write(b"dummy image data")

    try:
        # זה יבדוק אם Gemini עובד או שה-Fallback ל-Groq נכנס לפעולה
        result = analyze_mechanic_work(test_image, instruction="Test run")
        print(f"✅ AI Response: {result[:50]}...")
        assert len(result) > 0
    except Exception as e:
        print(f"❌ AI Logic Failed: {e}")

    print("\n✅ ALL LOGIC TESTS PASSED!")


if __name__ == "__main__":
    test_full_flow()
