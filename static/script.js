let socket = null;
let isConnected = false;
let errorTimeout = null;

// Global variables for managing recording state
let isRecording = false;
let recognition = null;

function updateConnectionStatus(connected) {
    isConnected = connected;
    const indicator = document.querySelector('.connection-indicator');
    const statusText = document.querySelector('.connection-status span');
    
    if (connected) {
        indicator.classList.remove('disconnected');
        indicator.classList.add('connected');
        statusText.textContent = 'Connected';
    } else {
        indicator.classList.remove('connected');
        indicator.classList.add('disconnected');
        statusText.textContent = 'Disconnected';
    }
}

function showError(message) {
    const errorElement = document.querySelector('.error-message');
    errorElement.textContent = message;
    errorElement.style.display = 'block';
    
    if (errorTimeout) {
        clearTimeout(errorTimeout);
    }
    
    errorTimeout = setTimeout(() => {
        errorElement.style.display = 'none';
    }, 5000);
}

function connectSocket() {
    if (socket) {
        socket.disconnect();
    }
    
    // Create Socket.IO instance with the current window location
    const serverUrl = window.location.protocol + '//' + window.location.hostname + ':' + window.location.port;
    socket = io(serverUrl, {
        transports: ['websocket'],
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
        timeout:5000,
        forceNew:true
    });
    
    socket.on('connect', () => {
        console.log('Connected to server');
        updateConnectionStatus(true);
        showError('');
    });
    
    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        updateConnectionStatus(false);
        showError('Connection lost. Please try reconnecting.');
    });
    
    socket.on('connect_error', (error) => {
        console.error('Connection error:', error);
        updateConnectionStatus(false);
        showError('Connection error occurred. Please try reconnecting.');
    });

    socket.on('error', (error) => {
        console.error('Socket error:', error);
        updateConnectionStatus(false);
        showError('Connection error occurred. Please try reconnecting.');
    });
    
    socket.on('connected', (data) => {
        console.log('Server connection established:', data);
    });
    
    socket.on('question', (data) => {
        console.log('Question received:', data);
        const questionDiv = document.getElementById('currentQuestion');
        if (questionDiv) {
            questionDiv.textContent = data.question;
        }
    });
    
    socket.on('email_details', (data) => {
        console.log('Email details received:', data);
        const emailDetails = document.getElementById('emailDetails');
        if (emailDetails) {
            emailDetails.style.display = 'block';
            document.getElementById('recipient').textContent = 'To: ' + data.details.recipient;
            document.getElementById('subject').textContent = 'Subject: ' + data.details.subject;
            document.getElementById('message').textContent = 'Message: ' + data.details.body;
        }
    });
    
    socket.on('result', (data) => {
        console.log('Result received:', data);
        const statusDiv = document.getElementById('status');
        if (statusDiv) {
            statusDiv.textContent = data.sent ? 'Email sent successfully!' : 'Email cancelled';
        }
    });
}

// Initialize connection when the page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('Page loaded, connecting to server...');
    connectSocket();
});

// Add event listener for reconnect button
document.querySelector('.reconnect-button').addEventListener('click', () => {
    console.log('Reconnecting...');
    connectSocket();
});

// Add event listeners for email actions
document.getElementById('startButton').addEventListener('click', () => {
    if (socket && isConnected) {
        socket.emit('start');
    }
});

document.getElementById('sendButton').addEventListener('click', () => {
    if (socket && isConnected) {
        socket.emit('confirm');
    }
});

document.getElementById('cancelButton').addEventListener('click', () => {
    if (socket && isConnected) {
        socket.emit('cancel');
    }
});

// Initialize the Web Speech API
function initializeSpeechRecognition() {
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        
        recognition.onresult = function(event) {
            const result = event.results[event.results.length - 1];
            if (result.isFinal) {
                const text = result.item(0).transcript;
                const activeInput = document.querySelector(':focus');
                if (activeInput) {
                    // Append new text to existing content
                    activeInput.value += ' ' + text;
                }
            }
        };
        
        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            stopRecording();
        };
    } else {
        alert('Speech recognition is not supported in this browser. Please use Chrome.');
    }
}

// Function to toggle recording state
function toggleRecording(button) {
    if (!recognition) {
        initializeSpeechRecognition();
    }
    
    if (!isRecording) {
        // Start recording
        recognition.start();
        isRecording = true;
        button.classList.add('listening');
        button.innerHTML = '<i class="fas fa-microphone"></i> Stop';
    } else {
        // Stop recording
        stopRecording();
    }
}

// Function to stop recording
function stopRecording() {
    if (recognition) {
        recognition.stop();
    }
    isRecording = false;
    const buttons = document.querySelectorAll('.voice-button');
    buttons.forEach(button => {
        button.classList.remove('listening');
        button.innerHTML = '<i class="fas fa-microphone"></i>';
    });
}

// Event listener for page unload to cleanup
window.addEventListener('beforeunload', function() {
    if (recognition) {
        recognition.stop();
    }
});

// ... existing code ... 