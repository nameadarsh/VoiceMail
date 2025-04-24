import os
import platform
from pathlib import Path
from typing import Dict, Any

class Config:
    """Application configuration class"""
    
    # Base paths
    BASE_DIR = Path(__file__).parent.parent
    CONFIG_DIR = BASE_DIR / "config"
    LOGS_DIR = BASE_DIR / "logs"
    
    # Ensure directories exist
    CONFIG_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    
    # Security
    SECRET_KEY = os.urandom(24)
    ENCRYPTION_KEY_PATH = CONFIG_DIR / "secret.key"
    PASSWORD_FILE_PATH = CONFIG_DIR / "email_pass.bin"
    
    # Application
    PORT = 8081
    HOST = "localhost"
    DEBUG = True
    
    # Email
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    
    # Audio
    MICROPHONE_INDEX = -1  # -1 for auto-detect
    SPEECH_TIMEOUT = 5
    MAX_RETRIES = 3
    
    # Browser paths based on OS
    CHROME_PATHS = {
        "Windows": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Users\%USERNAME%\AppData\Local\Google\Chrome\Application\chrome.exe"
        ],
        "Darwin": [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        ],
        "Linux": [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable"
        ]
    }
    
    # Email contacts (can be loaded from external file later)
    EMAIL_CONTACTS = {
        "ojasvi": "ojasvivok@gmail.com",
        "dia": "diasehra22.set@modyuniversity.ac.in",
        "dia sehra": "diasehra22.set@modyuniversity.ac.in",
        "self": "me@example.com",
    }
    
    @classmethod
    def get_chrome_path(cls) -> str:
        """Get Chrome browser path based on OS"""
        system = platform.system()
        paths = cls.CHROME_PATHS.get(system, [])
        
        for path in paths:
            expanded_path = os.path.expandvars(path)
            if os.path.exists(expanded_path):
                return expanded_path
        
        return None
    
    @classmethod
    def get_log_file(cls) -> Path:
        """Get path to log file"""
        return cls.LOGS_DIR / "app.log"
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get all configuration as dictionary"""
        return {
            key: value for key, value in cls.__dict__.items()
            if not key.startswith('_') and not callable(value)
        }

# Create instance
config = Config() 