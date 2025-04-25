"""
VoiceMail - A Voice-Controlled Email Assistant

This application provides a voice-controlled interface for composing and sending emails.
It uses Flask for the web server, SocketIO for real-time communication, and various
Google Cloud services for speech recognition and text-to-speech capabilities.

Key Features:
- Voice-controlled email composition
- Real-time speech recognition
- Secure email handling
- Web-based interface
- Cross-platform compatibility

Dependencies:
- Flask: Web framework
- Flask-SocketIO: Real-time communication
- Eventlet: Async server
- SpeechRecognition: Speech-to-text
- Google Cloud Speech: Enhanced speech recognition
- Google Cloud Text-to-Speech: Voice synthesis
- python-dotenv: Environment variable management
"""

# Monkey patch at the very beginning for async support
import eventlet
eventlet.monkey_patch()

# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading
import webbrowser
import os
import platform
import subprocess
import socket
import sys
from functools import wraps
from engineio.payload import Payload
from datetime import timedelta
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

from src.config import config
from src.utils.logger import logger
from src.audio.speech import speech_manager
from src.email.manager import email_manager
from src.security.encryption import encryption_manager

# Increase max packet size
Payload.max_decode_packets = 50

# Load environment variables
load_dotenv()

# Initialize Flask app
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
app = Flask(__name__, template_folder=template_dir, static_folder="static")
app.secret_key = os.urandom(24)

# Initialize CORS
CORS(app, resources={
    r"/*": {
        "origins": [f"http://{config.HOST}:{config.PORT}"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize SocketIO
socketio = SocketIO(
    app,
    cors_allowed_origins=[f"http://{config.HOST}:{config.PORT}"],
    async_mode='eventlet',
    logger=True,
    engineio_logger=True,
    ping_timeout=60000,
    ping_interval=25000,
    max_http_buffer_size=1e8,
    manage_session=True,
    always_connect=True,
    reconnection=True,
    reconnection_attempts=5,
    reconnection_delay=1000,
    transports=['websocket', 'polling']
)

# Store active email assistant sessions
active_sessions = {}

# Add thread lock for thread safety
thread_lock = threading.Lock()
thread = None

def with_app_context(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        with app.app_context():
            return f(*args, **kwargs)
    return wrapped

def open_browser(port: int):
    """Open browser with appropriate configuration"""
    try:
        url = f"http://{config.HOST}:{port}/"
        logger.info(f"Attempting to open browser at: {url}")
        
        chrome_path = config.get_chrome_path()
        if chrome_path:
            # Create a separate Chrome profile directory
            profile_dir = os.path.abspath("./chrome-profile")
            if not os.path.exists(profile_dir):
                os.makedirs(profile_dir)
            
            # Browser flags
            flags = [
                chrome_path,
                url,
                '--use-fake-ui-for-media-stream',
                f'--user-data-dir={profile_dir}',
                '--autoplay-policy=no-user-gesture-required',
                '--enable-speech-dispatcher',
                '--enable-speech-input',
                '--enable-experimental-web-platform-features',
                '--allow-file-access-from-files',
                '--allow-running-insecure-content'
            ]
            
            if config.DEBUG:
                flags.extend([
                    '--ignore-certificate-errors'
                ])
            
            logger.info("Launching browser with flags:")
            for flag in flags[1:]:
                logger.info(f"  {flag}")
            
            subprocess.Popen(flags)
        else:
            logger.warning("Chrome not found in standard locations")
            logger.info(f"Please manually open {url} in Chrome")
            logger.info("Make sure to:")
            logger.info("1. Allow microphone access when prompted")
            logger.info("2. Allow audio autoplay")
            logger.info("3. Enable experimental web platform features")
            
    except Exception as e:
        logger.error(f"Error opening browser: {e}")
        logger.info(f"Please manually open {url} in Chrome")

def send_email(from_email, password, to_email, subject, body):
    """Send email using Gmail SMTP"""
    try:
        # Create message
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email

        # Send email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(from_email, password)
            server.send_message(msg)
        return True, "Email sent successfully!"
    except Exception as e:
        return False, str(e)

@app.route("/", methods=["GET", "POST"])
def login():
    """Handle login page"""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        if not email or not password:
            flash("Please enter both email and app password")
            return render_template("login.html")
            
        if not "@gmail.com" in email:
            flash("Please enter a valid Gmail address")
            return render_template("login.html")
        
        # Store credentials in session
        session["email"] = email
        session["password"] = password
        return redirect(url_for("compose"))
        
    return render_template("login.html")

@app.route("/compose")
def compose():
    """Handle email composition page"""
    if "email" not in session:
        flash("Please login first")
        return redirect(url_for("login"))
    return render_template("compose.html", email=session["email"])

@socketio.on("connect")
def handle_connect():
    """Handle client connection"""
    if "email" not in session:
        return False
    emit("connected", {"email": session["email"]})

@socketio.on("send_email")
def handle_send_email(data):
    """Handle email sending"""
    try:
        to_email = data.get("to")
        subject = data.get("subject")
        body = data.get("body")
        
        if not all([to_email, subject, body]):
            emit("error", {"message": "Missing email details"})
            return
            
        success, message = send_email(
            session["email"],
            session["password"],
            to_email,
            subject,
            body
        )
        
        emit("email_result", {
            "success": success,
            "message": message
        })
        
    except Exception as e:
        emit("error", {"message": str(e)})

def is_client_connected(sid: str) -> bool:
    """Check if client is still connected"""
    try:
        return sid in active_sessions and socketio.server.manager.rooms.get('/', {}).get(sid)
    except Exception as e:
        logger.error(f"Error checking connection status: {e}")
        return False

def background_thread(sid, email_user):
    """Background thread for email assistant"""
    global thread
    logger.info(f'Starting background thread for {email_user}')
    
    try:
        # Store state in a thread-safe way
        with thread_lock:
            if sid not in active_sessions:
                logger.error("No active session found")
                return
                
            # Start conversation
            contacts_str = ", ".join(config.EMAIL_CONTACTS.keys())
            question = f"Who would you like to send the email to? You can say a contact name ({contacts_str}) or a full email address."
            
            # Store initial state
            active_sessions[sid + '_state'] = {
                'state': 'recipient',
                'email_user': email_user
            }
            
            # Send initial question
            socketio.emit('question', {'question': question}, room=sid)
            
    except Exception as e:
        logger.error(f'Error in background thread: {e}')
        if sid in active_sessions:
            socketio.emit('error', {'message': str(e)}, room=sid)
    finally:
        thread = None

@socketio.on('disconnect')
def handle_disconnect(sid=None):
    """Handle client disconnect"""
    logger.info('\n=== Client disconnected ===')
    sid = request.sid if sid is None else sid
    logger.info(f'Session ID: {sid}')
    try:
        with thread_lock:
            if sid in active_sessions:
                del active_sessions[sid]
            if sid + '_state' in active_sessions:
                del active_sessions[sid + '_state']
    except Exception as e:
        logger.error(f'Error cleaning up session: {e}')

@socketio.on_error_default
def default_error_handler(e):
    """Handle all socket.io errors"""
    logger.error(f'\n=== Socket.IO error: {str(e)} ===')
    sid = request.sid
    error_msg = str(e) if str(e) else 'Unknown error occurred'
    logger.error(f'Error details for session {sid}: {error_msg}')
    try:
        emit('error', {'message': error_msg})
        if sid in active_sessions:
            del active_sessions[sid]
    except Exception as error:
        logger.error(f'Error in error handler: {error}')

@socketio.on('start')
def handle_start():
    """Start email assistant session"""
    global thread
    
    logger.info('\n=== Starting new email session ===')
    
    # Verify user is logged in
    email_user = session.get('email')
    if not email_user:
        logger.error("Unauthorized start attempt")
        emit('error', {'message': 'Please login first'})
        return

    sid = request.sid
    logger.info(f'Session ID: {sid}')

    # Clean up any existing session
    if sid in active_sessions:
        del active_sessions[sid]

    def email_assistant_callback(question=None, details=None, result=None):
        try:
            if not is_client_connected(sid):
                logger.warning(f"Client {sid} disconnected, stopping callback")
                return
                
            if question:
                socketio.emit('question', {'question': question}, room=sid)
            if details:
                socketio.emit('email_details', {'details': details}, room=sid)
            if result:
                socketio.emit('result', result, room=sid)
        except Exception as e:
            logger.error(f'Error in callback: {e}')
            socketio.emit('error', {'message': str(e)}, room=sid)

    active_sessions[sid] = email_assistant_callback
    
    try:
        with thread_lock:
            if thread is None:
                thread = socketio.start_background_task(
                    target=background_thread,
                    sid=sid,
                    email_user=email_user
                )
        emit('started', {
            'status': 'Email assistant started',
            'email': email_user
        })
        logger.info(f"Email assistant started for {email_user}")
    except Exception as e:
        logger.error(f'Error starting email assistant: {e}')
        emit('error', {'message': str(e)})

@socketio.on('response')
def handle_response(data):
    """Handle voice response from client"""
    logger.info('\n=== Voice response received ===')
    sid = request.sid
    
    if not sid in active_sessions:
        logger.error("No active session found")
        emit('error', {'message': 'No active session found'})
        return
        
    try:
        text = data.get('text', '').strip()
        logger.info(f'Response text: {text}')
        
        if not text:
            emit('error', {'message': 'Empty response received'})
            return
            
        # Get session state in thread-safe way
        with thread_lock:
            session_state = active_sessions.get(sid + '_state', {})
            state = session_state.get('state', 'recipient')
            email_user = session_state.get('email_user')
            
            if not email_user:
                emit('error', {'message': 'Session state lost'})
                return
            
            # Process response based on state
            if state == 'recipient':
                # Process recipient
                if '@' in text:
                    to = text
                elif text.lower() in config.EMAIL_CONTACTS:
                    to = config.EMAIL_CONTACTS[text.lower()]
                else:
                    contacts_str = ", ".join(config.EMAIL_CONTACTS.keys())
                    emit('question', {'question': f"I don't recognize that contact. Please say a full email address or one of: {contacts_str}"})
                    return
                
                # Update state
                session_state['to'] = to
                session_state['state'] = 'subject'
                active_sessions[sid + '_state'] = session_state
                emit('question', {'question': 'What is the subject of your email?'})
                
            elif state == 'subject':
                # Store subject and move to body
                session_state['subject'] = text
                session_state['state'] = 'body'
                active_sessions[sid + '_state'] = session_state
                emit('question', {'question': 'What message would you like to send? Take your time, I\'ll listen until you\'re done.'})
                
            elif state == 'body':
                # Store body and show preview
                session_state['body'] = text
                session_state['state'] = 'confirm'
                active_sessions[sid + '_state'] = session_state
                
                email_details = {
                    'to': session_state['to'],
                    'subject': session_state['subject'],
                    'body': text
                }
                emit('email_details', {'details': email_details})
                
            elif state == 'confirm':
                # Handle confirmation
                if 'yes' in text.lower():
                    # Send email
                    ok, info = email_manager.send_email(
                        email_user,
                        session_state['to'],
                        session_state['subject'],
                        session_state['body']
                    )
                    
                    result = {
                        'to': session_state['to'],
                        'subject': session_state['subject'],
                        'body': session_state['body'],
                        'sent': ok,
                        'info': info
                    }
                    
                    # Clean up session
                    del active_sessions[sid + '_state']
                    emit('result', result)
                else:
                    # Cancel email
                    del active_sessions[sid + '_state']
                    emit('result', {
                        'sent': False,
                        'info': 'Email cancelled'
                    })
            
    except Exception as e:
        logger.error(f'Error handling response: {e}')
        emit('error', {'message': str(e)})

@socketio.on('confirm')
def handle_confirm():
    """Handle email confirmation"""
    sid = request.sid
    if sid in active_sessions:
        callback = active_sessions[sid]
        callback(result={'sent': True})
    else:
        emit('error', {'message': 'No active session'})

@socketio.on('cancel')
def handle_cancel():
    """Handle email cancellation"""
    sid = request.sid
    if sid in active_sessions:
        callback = active_sessions[sid]
        callback(result={'sent': False})
    else:
        emit('error', {'message': 'No active session'})

def is_port_in_use(port: int) -> bool:
    """Check if port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((config.HOST, port)) == 0

def email_assistant(email_user: str, callback=None):
    """Main email assistant function"""
    logger.info("Starting email assistant")
    
    # Check password
    if not email_manager.password:
        error_msg = "App password missing. Please run set_password.py first."
        logger.error(error_msg)
        if callback:
            callback(None, None, {"error": error_msg})
        return {"error": error_msg}

    # Start conversation
    logger.info("Starting conversation")
    speech_manager.speak(f"I will help you send an email from {email_user}")

    # Get recipient
    contacts_str = ", ".join(config.EMAIL_CONTACTS.keys())
    recipient_prompt = f"Who would you like to send the email to? You can say a contact name ({contacts_str}) or a full email address."
    
    if callback:
        callback(recipient_prompt, None, None)
    
    to = None
    attempts = 0
    while not to and attempts < 3:
        attempts += 1
        logger.info(f"Recipient attempt {attempts}")
        name = speech_manager.listen(timeout=7)
        
        if name:
            if '@' in name:
                to = name
                logger.info(f"Using email address: {to}")
            elif name in config.EMAIL_CONTACTS:
                to = config.EMAIL_CONTACTS[name]
                logger.info(f"Using contact email: {to}")
                speech_manager.speak(f"Using email address: {to}")
            else:
                retry_prompt = f"I don't recognize that contact. Please say a full email address or one of: {contacts_str}"
                logger.info("Contact not recognized")
                if callback:
                    callback(retry_prompt, None, None)
                speech_manager.speak(retry_prompt)

    if not to:
        error_msg = "Could not get recipient email address"
        logger.error(error_msg)
        if callback:
            callback(None, None, {"error": error_msg})
        return {"error": error_msg}

    # Get subject
    subject_prompt = "What is the subject of your email?"
    logger.info("Asking for subject")
    if callback:
        callback(subject_prompt, None, None)
    
    subj = speech_manager.listen_with_retry(subject_prompt)
    if not subj:
        error_msg = "Could not get email subject"
        logger.error(error_msg)
        if callback:
            callback(None, None, {"error": error_msg})
        return {"error": error_msg}

    # Get message
    message_prompt = "What message would you like to send? Take your time, I'll listen until you're done."
    logger.info("Asking for message")
    if callback:
        callback(message_prompt, None, None)
    
    body = speech_manager.listen_with_retry("Please speak your message now.", timeout=10)
    if not body:
        error_msg = "Could not get email message"
        logger.error(error_msg)
        if callback:
            callback(None, None, {"error": error_msg})
        return {"error": error_msg}

    # Show email details
    email_details = {
        "recipient": to,
        "subject": subj,
        "body": body
    }
    
    logger.info("Showing email details")
    if callback:
        callback(None, email_details, None)
    
    speech_manager.speak("Here's your email details:")
    speech_manager.speak(f"To: {to}")
    speech_manager.speak(f"Subject: {subj}")
    speech_manager.speak(f"Message: {body}")

    # Confirm
    confirm_prompt = "Should I send this email? Say yes or no."
    logger.info("Asking for confirmation")
    if callback:
        callback(confirm_prompt, None, None)
    
    confirm = speech_manager.listen_with_retry("Please say yes to send or no to cancel.")
    logger.info(f"Received confirmation: {confirm}")

    if confirm and 'yes' in confirm:
        logger.info("Sending email")
        ok, info = email_manager.send_email(email_user, to, subj, body)
    else:
        logger.info("Email cancelled")
        ok, info = False, "Email cancelled"

    result = {
        "to": to,
        "subject": subj,
        "body": body,
        "sent": ok,
        "info": info
    }

    logger.info(f"Final result: {result}")
    if callback:
        callback(None, None, result)
    return result

if __name__ == "__main__":
    logger.info("\n" + "="*60)
    logger.info("Voice Email Assistant Server Starting")
    logger.info("="*60)
    
    if is_port_in_use(config.PORT):
        logger.error(f"Error: Port {config.PORT} is already in use!")
        logger.error("Please make sure no other application is using this port.")
        sys.exit(1)
    
    try:
        logger.info("\nStarting server with configuration:")
        logger.info(f"- Port: {config.PORT}")
        logger.info(f"- Debug: {config.DEBUG}")
        logger.info("- Transport: websocket, polling")
        
        # Open browser
        open_browser(config.PORT)
        
        # Start server with eventlet
        socketio.run(
            app,
            host=config.HOST,
            port=config.PORT,
            debug=config.DEBUG,
            use_reloader=False,
            log_output=True
        )
    except Exception as e:
        logger.error(f"\nError starting server: {e}")
        sys.exit(1)