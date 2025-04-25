from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from src.email.manager import EmailManager
from src.security.encryption import encrypt_password, check_password
from src.audio.speech import process_audio
from src.utils.logger import setup_logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Setup logging
logger = setup_logger()

# Initialize email manager
email_manager = EmailManager()

@app.route('/')
def index():
    if 'email' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        if email_manager.verify_credentials(email, password):
            session['email'] = email
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/compose', methods=['GET', 'POST'])
def compose():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        to_email = request.form['to']
        subject = request.form['subject']
        message = request.form['message']
        
        try:
            email_manager.send_email(session['email'], to_email, subject, message)
            flash('Email sent successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error sending email: {str(e)}', 'error')
    
    return render_template('compose.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8081))
    app.run(host='0.0.0.0', port=port, debug=True) 