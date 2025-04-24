import smtplib
from email.message import EmailMessage
from typing import Optional, Dict, Any, Tuple

from ..config import config
from ..utils.logger import logger
from ..security.encryption import encryption_manager

class EmailManager:
    """Handles email operations"""
    
    def __init__(self):
        """Initialize email manager"""
        self.password = None
        self._load_password()
    
    def _load_password(self) -> bool:
        """Load email password"""
        try:
            self.password = encryption_manager.load_password()
            if not self.password:
                logger.error("Failed to load email password")
                return False
            return True
        except Exception as e:
            logger.error(f"Error loading email password: {e}")
            return False
    
    def set_password(self, password: str) -> bool:
        """Set and save email password"""
        try:
            if not password:
                logger.error("Cannot set empty password")
                return False
            
            if encryption_manager.save_password(password):
                self.password = password
                return True
            return False
        except Exception as e:
            logger.error(f"Error setting password: {e}")
            return False
    
    def create_smtp_connection(self) -> Optional[smtplib.SMTP]:
        """Create SMTP connection with retry"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting SMTP connection (attempt {attempt + 1})")
                server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
                server.starttls()
                return server
            except Exception as e:
                logger.error(f"SMTP connection error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    continue
                return None
    
    def send_email(self, from_email: str, to_email: str, subject: str, body: str) -> Tuple[bool, str]:
        """Send email with error handling"""
        if not self.password:
            error_msg = "Email password not set"
            logger.error(error_msg)
            return False, error_msg
        
        try:
            # Create message
            msg = EmailMessage()
            msg["From"] = from_email
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.set_content(body)
            
            # Create SMTP connection
            server = self.create_smtp_connection()
            if not server:
                error_msg = "Failed to create SMTP connection"
                logger.error(error_msg)
                return False, error_msg
            
            try:
                # Login and send
                logger.info("Logging in to SMTP server")
                server.login(from_email, self.password)
                logger.info("Sending email")
                server.send_message(msg)
                logger.info("Email sent successfully")
                return True, "Email sent successfully"
            finally:
                server.quit()
                
        except smtplib.SMTPAuthenticationError:
            error_msg = "SMTP authentication failed"
            logger.error(error_msg)
            return False, error_msg
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error sending email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_contact_email(self, name: str) -> Optional[str]:
        """Get email address for a contact name"""
        return config.EMAIL_CONTACTS.get(name.lower())
    
    def is_valid_email(self, email: str) -> bool:
        """Check if email address is valid"""
        return '@' in email and '.' in email.split('@')[1]

# Create global email manager instance
email_manager = EmailManager() 