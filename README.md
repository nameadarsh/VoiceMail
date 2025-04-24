# Voice Email Assistant

A voice-controlled email assistant that allows users to compose and send emails using voice commands.

## Features

- Voice-to-text email composition
- Text-to-speech feedback
- Real-time email preview
- Secure Gmail integration using App Passwords
- Web-based interface with modern UI
- Cross-platform compatibility

## Prerequisites

- Python 3.8 or higher
- Google Account with 2-Step Verification enabled
- App Password from Google Account
- Chrome browser (recommended for best voice recognition)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd PythonProject
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Start the application:
```bash
python app.py
```

2. The application will automatically open your default browser to `http://localhost:8081/`

3. To use the application:
   - Log in with your Gmail address and App Password
   - Follow the voice prompts to compose your email
   - Review the email preview
   - Confirm to send or cancel

## Stopping the Application

1. To stop the application:
   - Press `Ctrl+C` in the terminal where the application is running
   - Or use Task Manager to end the Python process

2. If the application doesn't stop properly:
   - On Windows: Open Task Manager and end the Python process
   - On Linux/Mac: Use `pkill python` or `killall python`

## Security Notes

- The application uses Google's App Passwords for secure authentication
- No passwords are stored locally
- All voice data is processed locally
- SSL/TLS encryption is used for all communications

## Troubleshooting

1. If voice recognition isn't working:
   - Ensure you're using Chrome browser
   - Check microphone permissions
   - Verify your microphone is properly connected

2. If login fails:
   - Verify your App Password is correct
   - Ensure 2-Step Verification is enabled
   - Check your internet connection

3. If the application crashes:
   - Check the terminal for error messages
   - Verify all dependencies are installed
   - Restart the application

## Development

- The application uses Flask for the backend
- Socket.IO for real-time communication
- Web Speech API for voice recognition
- pyttsx3 for text-to-speech

## License

This project is licensed under the MIT License - see the LICENSE file for details. 