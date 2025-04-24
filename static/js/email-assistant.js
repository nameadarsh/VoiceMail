class EmailAssistant {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.currentState = 'ready';
        this.stateChangeCallbacks = [];
        this.messageCallbacks = [];
        this.errorCallbacks = [];
        this.emailDetails = null;
        this.isProcessing = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.autoReconnect = true;
        
        // Connect when the document is ready
        if (document.readyState === 'complete') {
            this.initializeSocket();
        } else {
            document.addEventListener('DOMContentLoaded', () => this.initializeSocket());
        }

        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible' && !this.isConnected && this.autoReconnect) {
                this.reconnect();
            }
        });
    }

    initializeSocket() {
        if (!window.io) {
            console.error('Socket.IO not loaded');
            this.handleError('Socket.IO library not loaded');
            return;
        }

        try {
            // Clean up existing socket if any
            if (this.socket) {
                this.socket.disconnect();
                this.socket = null;
            }

            // Create new socket with robust configuration
            this.socket = io({
                transports: ['websocket', 'polling'],
                upgrade: true,
                reconnection: true,
                reconnectionAttempts: this.maxReconnectAttempts,
                reconnectionDelay: this.reconnectDelay,
                timeout: 20000,
                forceNew: true,
                autoConnect: true
            });

            this.setupSocketListeners();
        } catch (error) {
            console.error('Failed to initialize socket:', error);
            this.handleError('Failed to initialize connection: ' + error.message);
        }
    }

    setupSocketListeners() {
        if (!this.socket) return;

        // Connection events
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.updateState({ currentStep: 'connected' });
        });

        this.socket.on('disconnect', (reason) => {
            console.log('Disconnected from server:', reason);
            this.isConnected = false;
            this.updateState({ currentStep: 'disconnected' });

            // Handle different disconnect reasons
            if (reason === 'io server disconnect') {
                // Server initiated disconnect, don't attempt to reconnect
                this.autoReconnect = false;
            } else if (this.autoReconnect) {
                this.reconnect();
            }
        });

        this.socket.on('connect_error', (error) => {
            console.error('Connection error:', error);
            this.handleError('Connection error: ' + error.message);
            if (this.autoReconnect) {
                this.reconnect();
            }
        });

        this.socket.on('error', (error) => {
            console.error('Socket error:', error);
            this.handleError('Socket error: ' + error.message);
        });

        // Application events with error handling
        this.socket.on('started', (data) => {
            try {
                console.log('Email process started:', data);
                this.updateState({ currentStep: 'starting' });
            } catch (error) {
                this.handleError('Error processing start event: ' + error.message);
            }
        });

        this.socket.on('question', (data) => {
            try {
                console.log('Question received:', data);
                this.updateState({ 
                    currentStep: 'asking',
                    currentQuestion: data.question
                });
            } catch (error) {
                this.handleError('Error processing question: ' + error.message);
            }
        });

        this.socket.on('email_details', (data) => {
            try {
                console.log('Email details received:', data);
                this.emailDetails = data.details;
                this.updateState({ 
                    currentStep: 'confirming',
                    emailDetails: data.details
                });
            } catch (error) {
                this.handleError('Error processing email details: ' + error.message);
            }
        });

        this.socket.on('result', (data) => {
            try {
                console.log('Result received:', data);
                this.updateState({ 
                    currentStep: 'completed',
                    result: data
                });
            } catch (error) {
                this.handleError('Error processing result: ' + error.message);
            }
        });
    }

    reconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            this.autoReconnect = false;
            this.handleError('Maximum reconnection attempts reached');
            return;
        }

        this.reconnectAttempts++;
        console.log(`Reconnection attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
        
        setTimeout(() => {
            if (!this.isConnected) {
                this.initializeSocket();
            }
        }, this.reconnectDelay * this.reconnectAttempts);
    }

    connect() {
        this.autoReconnect = true;
        if (!this.socket || !this.isConnected) {
            this.initializeSocket();
        }
    }

    startEmailProcess() {
        if (!this.isConnected) {
            this.handleError('Not connected to server');
            return;
        }

        if (this.isProcessing) {
            this.handleError('Email process already in progress');
            return;
        }

        console.log('Starting email process');
        this.isProcessing = true;
        this.socket.emit('start');
    }

    sendResponse(text) {
        if (!this.isConnected) {
            this.handleError('Not connected to server');
            return;
        }

        if (!text) {
            this.handleError('No text to send');
            return;
        }

        console.log('Sending response:', text);
        this.socket.emit('response', { text: text });
    }

    confirmEmail() {
        if (!this.isConnected) {
            this.handleError('Not connected to server');
            return;
        }

        console.log('Confirming email');
        this.socket.emit('confirm');
        this.isProcessing = false;
    }

    cancelEmail() {
        if (!this.isConnected) {
            this.handleError('Not connected to server');
            return;
        }

        console.log('Cancelling email');
        this.socket.emit('cancel');
        this.isProcessing = false;
    }

    handleError(error) {
        console.error('Error:', error);
        this.updateState({ 
            currentStep: 'error',
            error: error
        });
        this.notifyError(error);
    }

    updateState(newState) {
        this.currentState = { ...this.currentState, ...newState };
        this.stateChangeCallbacks.forEach(callback => {
            try {
                callback(this.currentState);
            } catch (error) {
                console.error('Error in state change callback:', error);
            }
        });
    }

    onStateChange(callback) {
        if (callback && typeof callback === 'function') {
            this.stateChangeCallbacks.push(callback);
        }
    }

    onError(callback) {
        if (callback && typeof callback === 'function') {
            this.errorCallbacks.push(callback);
        }
    }

    notifyError(error) {
        this.errorCallbacks.forEach(callback => {
            try {
                callback(error);
            } catch (error) {
                console.error('Error in error callback:', error);
            }
        });
    }
} 