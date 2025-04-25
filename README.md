# VoiceMail - Voice-Controlled Email Assistant

## Overview
VoiceMail is a voice-controlled email assistant that allows users to compose and send emails using voice commands. It provides a web-based interface with real-time speech recognition and text-to-speech capabilities.

## Features
- Voice-controlled email composition
- Real-time speech recognition
- Secure email handling
- Web-based interface
- Cross-platform compatibility
- Chrome browser integration
- Session management
- Error handling and logging

## Project Structure
```
PythonProject/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables (not tracked by git)
├── .gitignore            # Git ignore rules
├── chrome-profile/       # Chrome browser profile
├── config/              # Configuration files
├── logs/                # Application logs
├── src/                 # Source code
│   ├── audio/          # Speech-related modules
│   ├── email/          # Email handling modules
│   ├── security/       # Security-related modules
│   └── utils/          # Utility functions
├── static/             # Static files (CSS, JS, images)
├── templates/          # HTML templates
└── tests/             # Test files
```

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Chrome browser
- Google Cloud account (for speech services)
- Gmail account with App Password enabled

### Installation
1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with the following variables:
   ```
   HOST=localhost
   PORT=5000
   DEBUG=True
   GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json
   ```

### Files Not Tracked by Git
The following files need to be shared manually with other developers:
1. `.env` - Contains environment variables and sensitive configuration
2. `credentials.json` - Google Cloud credentials file
3. `encryption.key` - Encryption key for secure data handling
4. `chrome-profile/` - Chrome browser profile directory

### Running the Application
1. Activate the virtual environment
2. Run the application:
   ```bash
   python app.py
   ```
3. The application will automatically open Chrome with the correct configuration

## Security Considerations
- Never commit sensitive files to git
- Use environment variables for configuration
- Enable Gmail App Password for secure email access
- Keep encryption keys secure
- Regularly update dependencies

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details. 