import os
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet

from ..config import config
from ..utils.logger import logger

class EncryptionManager:
    """Handles encryption and decryption of sensitive data"""
    
    def __init__(self):
        """Initialize encryption manager"""
        self.key = self._load_or_create_key()
        self.fernet = Fernet(self.key)
    
    def _load_or_create_key(self) -> bytes:
        """Load encryption key or create a new one"""
        try:
            if config.ENCRYPTION_KEY_PATH.exists():
                logger.info("Loading existing encryption key")
                return config.ENCRYPTION_KEY_PATH.read_bytes()
            else:
                logger.info("Creating new encryption key")
                key = Fernet.generate_key()
                config.ENCRYPTION_KEY_PATH.write_bytes(key)
                return key
        except Exception as e:
            logger.error(f"Error handling encryption key: {e}")
            raise
    
    def encrypt(self, data: str) -> bytes:
        """Encrypt data"""
        try:
            return self.fernet.encrypt(data.encode())
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            raise
    
    def decrypt(self, encrypted_data: bytes) -> Optional[str]:
        """Decrypt data"""
        try:
            return self.fernet.decrypt(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            return None
    
    def save_password(self, password: str) -> bool:
        """Save encrypted password to file"""
        try:
            if not password:
                logger.error("Cannot save empty password")
                return False
            
            encrypted = self.encrypt(password)
            config.PASSWORD_FILE_PATH.write_bytes(encrypted)
            logger.info("Password saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving password: {e}")
            return False
    
    def load_password(self) -> Optional[str]:
        """Load and decrypt password from file"""
        try:
            if not config.PASSWORD_FILE_PATH.exists():
                logger.error("Password file not found")
                return None
            
            encrypted = config.PASSWORD_FILE_PATH.read_bytes()
            return self.decrypt(encrypted)
        except Exception as e:
            logger.error(f"Error loading password: {e}")
            return None

# Create global encryption manager instance
encryption_manager = EncryptionManager() 