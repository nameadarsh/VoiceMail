from cryptography.fernet import Fernet
import os
import logging

logger = logging.getLogger(__name__)

KEY_FILE = "encryption.key"

def generate_key():
    """Generate a new encryption key"""
    return Fernet.generate_key()

def save_key(key):
    """Save the encryption key to a file"""
    with open(KEY_FILE, 'wb') as key_file:
        key_file.write(key)

def load_key():
    """Load the encryption key from file"""
    try:
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, 'rb') as key_file:
                return key_file.read()
        else:
            # Generate a new key if none exists
            key = generate_key()
            save_key(key)
            return key
    except Exception as e:
        logger.error(f"Error loading encryption key: {e}")
        return None

def encrypt_password(password):
    """Encrypt a password"""
    try:
        key = load_key()
        if not key:
            return None
        f = Fernet(key)
        return f.encrypt(password.encode())
    except Exception as e:
        logger.error(f"Error encrypting password: {e}")
        return None

def decrypt_password(encrypted_password):
    """Decrypt a password"""
    try:
        key = load_key()
        if not key:
            return None
        f = Fernet(key)
        return f.decrypt(encrypted_password).decode()
    except Exception as e:
        logger.error(f"Error decrypting password: {e}")
        return None 