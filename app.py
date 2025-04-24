"""
Voice Email Assistant - Main Application File
This file serves as the entry point for the Voice Email Assistant application.
It sets up the Flask server, Socket.IO connections, and routes for the web interface.
"""

# Standard library imports
import os
import sys
import logging
import webbrowser
from threading import Timer

# Third-party imports
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_socketio import SocketIO
from flask_cors import CORS

# Local imports
from src.audio.speech import speech_manager
from src.email.email_manager import EmailManager
from src.utils.config import Config
from src.utils.logger import setup_logger

# Initialize logging
setup_logger()
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a random secret key for session management

# Enable CORS for all routes
CORS(app)

# Initialize Socket.IO with the Flask app
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Initialize email manager
email_manager = EmailManager()

# Configuration
config = Config()
PORT = config.get('server', 'port', 8081)
DEBUG = config.get('server', 'debug', True)

@app.route('/')
def index():
    """
    Main route handler for the application.
    Redirects to login if not authenticated, otherwise shows the main interface.
    """
    if 'email' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login route handler.
    GET: Shows the login form
    POST: Processes login credentials
    """
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # Attempt to login with provided credentials
            if email_manager.login(email, password):
                session['email'] = email
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid credentials. Please try again.', 'error')
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash('An error occurred during login. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """
    Logout route handler.
    Clears the session and redirects to login page.
    """
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@socketio.on('connect')
def handle_connect():
    """
    Socket.IO connection handler.
    Called when a client connects to the WebSocket.
    """
    logger.info('Client connected')
    socketio.emit('connected', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """
    Socket.IO disconnection handler.
    Called when a client disconnects from the WebSocket.
    """
    logger.info('Client disconnected')

@socketio.on('start')
def handle_start():
    """
    Handler for starting the email composition process.
    Initializes speech recognition and text-to-speech.
    """
    try:
        speech_manager.initialize()
        socketio.emit('question', {'question': 'Who would you like to email?'})
    except Exception as e:
        logger.error(f"Error starting email composition: {str(e)}")
        socketio.emit('error', {'message': 'Failed to initialize speech services'})

@socketio.on('confirm')
def handle_confirm():
    """
    Handler for confirming and sending the email.
    """
    try:
        if email_manager.send_email():
            socketio.emit('result', {'sent': True})
        else:
            socketio.emit('result', {'sent': False})
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        socketio.emit('error', {'message': 'Failed to send email'})

@socketio.on('cancel')
def handle_cancel():
    """
    Handler for canceling the email composition.
    """
    try:
        email_manager.cancel_email()
        socketio.emit('result', {'sent': False})
    except Exception as e:
        logger.error(f"Error canceling email: {str(e)}")
        socketio.emit('error', {'message': 'Failed to cancel email'})

def open_browser():
    """
    Opens the default web browser to the application URL.
    """
    url = f"http://localhost:{PORT}/"
    logger.info(f"Opening browser at: {url}")
    webbrowser.open(url)

if __name__ == '__main__':
    """
    Main entry point for the application.
    Sets up the server and opens the browser.
    """
    logger.info("\n" + "=" * 60)
    logger.info("Voice Email Assistant Server Starting")
    logger.info("=" * 60 + "\n")
    
    logger.info(f"Starting server with configuration:")
    logger.info(f"- Port: {PORT}")
    logger.info(f"- Debug: {DEBUG}")
    logger.info(f"- Transport: websocket, polling")
    
    # Open browser after a short delay
    Timer(1.5, open_browser).start()
    
    # Start the Socket.IO server
    socketio.run(app, host='0.0.0.0', port=PORT, debug=DEBUG)