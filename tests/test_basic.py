import unittest
from src.config import config
from src.utils.logger import logger
from src.security.encryption import encryption_manager
from src.email.manager import email_manager

class TestBasicFunctionality(unittest.TestCase):
    """Basic functionality tests"""
    
    def setUp(self):
        """Set up test environment"""
        logger.info("Setting up test environment")
    
    def test_config(self):
        """Test configuration loading"""
        self.assertIsNotNone(config.SECRET_KEY)
        self.assertIsNotNone(config.PORT)
        self.assertIsNotNone(config.HOST)
        self.assertTrue(config.CONFIG_DIR.exists())
        self.assertTrue(config.LOGS_DIR.exists())
    
    def test_encryption(self):
        """Test encryption functionality"""
        test_data = "test_password"
        encrypted = encryption_manager.encrypt(test_data)
        decrypted = encryption_manager.decrypt(encrypted)
        self.assertEqual(decrypted, test_data)
    
    def test_email_validation(self):
        """Test email validation"""
        self.assertTrue(email_manager.is_valid_email("test@example.com"))
        self.assertFalse(email_manager.is_valid_email("invalid_email"))
        self.assertFalse(email_manager.is_valid_email("test@"))
    
    def test_contact_lookup(self):
        """Test contact lookup"""
        self.assertEqual(
            email_manager.get_contact_email("ojasvi"),
            "ojasvivok@gmail.com"
        )
        self.assertIsNone(email_manager.get_contact_email("nonexistent"))

if __name__ == '__main__':
    unittest.main() 