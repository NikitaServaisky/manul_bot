import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

# Get the encryption key from environment variables
# To get generarate a key, you can run: Fernet.generate_key().decode()
ENCRPTION_KEY = os.getenv("FIELD_ENCRYPTION_KEY")

if not ENCRPTION_KEY:
    # Fallback for development only so the bot won't crash immediately
    # In production, ALWAYS set FIELD_ENCRIPTION_KEY in your .env file
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
        decrypted_text = chiper_suite.decrypt(data.encode())
        return decrypted_text.decode()
    except Exception:
        # If decryption fails (e.g bad key or unencrypted data), return original
        return data