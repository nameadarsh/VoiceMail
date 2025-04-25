from cryptography.fernet import Fernet
import os
from src.utils.logger import setup_logger

logger = setup_logger()

def generate_key():
    """Generate a new encryption key"""
    return Fernet.generate_key()

def encrypt_password(password):
    """Encrypt a password using Fernet symmetric encryption"""
    try:
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            key = generate_key()
            os.environ['ENCRYPTION_KEY'] = key.decode()
        
        f = Fernet(key if isinstance(key, bytes) else key.encode())
        encrypted_password = f.encrypt(password.encode())
        return encrypted_password
    except Exception as e:
        logger.error(f"Error encrypting password: {str(e)}")
        raise

def check_password(encrypted_password, password_attempt):
    """Check if a password attempt matches the encrypted password"""
    try:
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            logger.error("No encryption key found")
            return False
        
        f = Fernet(key if isinstance(key, bytes) else key.encode())
        decrypted_password = f.decrypt(encrypted_password).decode()
        return decrypted_password == password_attempt
    except Exception as e:
        logger.error(f"Error checking password: {str(e)}")
        return False 