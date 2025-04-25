import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import os
from src.utils.logger import setup_logger

logger = setup_logger()

class EmailManager:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self._credentials = {}
        
    def verify_credentials(self, email, app_password):
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(email, app_password)
                # Store credentials for later use
                self._credentials[email] = app_password
                return True
        except Exception as e:
            logger.error(f"Failed to verify credentials: {str(e)}")
            return False

    def send_email(self, from_email, to_email, subject, message):
        try:
            if from_email not in self._credentials:
                raise ValueError("User not authenticated. Please log in again.")

            msg = MIMEMultipart()
            msg['From'] = formataddr(("Voice Mail Assistant", from_email))
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(message, 'plain'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(from_email, self._credentials[from_email])
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            raise 