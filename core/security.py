import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

# Get the encryption key from environment variables
# To get generarate a key, you can run: Fernet.generate_key().decode()
ENCRPTION_KEY = os.getenv("FIELD_ENCRYPTION_KEY")

if not ENCRPTION_KEY:
    # Check if we are running in a local/dev environment or production
    # If it's a server environment, crash immediately to prevent data encryption
    if os.getenv("ENV_MODE") == "PRODUCTION":
        print("❌ ERROR: FIELD_ENCRYPTION_KEY is missing in production! Crashing to protect data.")
        sys.exit(1)
    else:
        print("⚠️ WARNING: FIELD_ENCRYPTION_KEY not found. Generating a temporary volatile key for development.")
        ENCRPTION_KEY = Fernet.generate_key().decode()

chiper_suite = Fernet(ENCRPTION_KEY.encode())

def encrypt_data(data: str) -> str:
    """ Encrypts a string using Fernet symmetric encryption."""
    if not data:
        return data
    encrypted_text = chiper_suite.encrypt(data.encode())
    return encrypted_text.decode()


def decrypt_data(data: str) -> str:
    """ Decrypts a Fernet encrypted string back to plain text."""
    if not data:
        return data
    try:
        # Try to decrypt assuming the string is Fernet encrypted tokens
        decrypted_text = chiper_suite.decrypt(data.encode())
        return decrypted_text.decode()
    except Exception:
        # Fallback for unencrypted legacy rows during migration phase
        return data