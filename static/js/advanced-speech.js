class AdvancedSpeechHandler {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.onResultCallback = null;
        this.onErrorCallback = null;
        this.onEndCallback = null;
        this.synthesis = window.speechSynthesis;
        this.isSpeaking = false;
        this.initializeSpeechRecognition();
    }

    initializeSpeechRecognition() {
        try {
            // Try different speech recognition implementations
            if ('webkitSpeechRecognition' in window) {
                this.recognition = new webkitSpeechRecognition();
            } else if ('SpeechRecognition' in window) {
                this.recognition = new SpeechRecognition();
            } else {
                throw new Error('Speech recognition not supported in this browser');
            }

            this.setupRecognition();
        } catch (error) {
            console.error('Speech recognition initialization error:', error);
            if (this.onErrorCallback) {
                this.onErrorCallback('Speech recognition not available: ' + error.message);
            }
        }
    }

    setupRecognition() {
        if (!this.recognition) return;

        // Configure recognition settings
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.maxAlternatives = 1;
        this.recognition.lang = 'en-US';

        // Handle results
        this.recognition.onresult = (event) => {
            try {
                const last = event.results.length - 1;
                const text = event.results[last][0].transcript;
                console.log('Recognized text:', text);
                
                if (this.onResultCallback && event.results[last].isFinal) {
                    this.onResultCallback(text);
                }
            } catch (error) {
                console.error('Error processing speech result:', error);
                if (this.onErrorCallback) {
                    this.onErrorCallback('Failed to process speech: ' + error.message);
                }
            }
        };

        // Handle errors
        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            let errorMessage = 'Speech recognition error: ';
            
            switch (event.error) {
                case 'no-speech':
                    errorMessage += 'No speech detected';
                    break;
                case 'aborted':
                    errorMessage += 'Recognition aborted';
                    break;
                case 'audio-capture':
                    errorMessage += 'No microphone detected';
                    break;
                case 'network':
                    errorMessage += 'Network error';
                    break;
                case 'not-allowed':
                    errorMessage += 'Microphone access denied';
                    break;
                default:
                    errorMessage += event.error;
            }
            
            if (this.onErrorCallback) {
                this.onErrorCallback(errorMessage);
            }
            
            // Auto-restart on certain errors
            if (['no-speech', 'audio-capture', 'network'].includes(event.error)) {
                setTimeout(() => this.restartRecognition(), 1000);
            }
        };

        // Handle end of recognition
        this.recognition.onend = () => {
            console.log('Speech recognition ended');
            this.isListening = false;
            if (this.onEndCallback) {
                this.onEndCallback();
            }
        };
    }

    startListening() {
        if (!this.recognition) {
            console.error('Speech recognition not initialized');
            if (this.onErrorCallback) {
                this.onErrorCallback('Speech recognition not initialized');
            }
            return;
        }

        // Stop any ongoing speech
        this.synthesis.cancel();

        try {
            // Reset recognition if it's already running
            if (this.isListening) {
                this.recognition.stop();
            }

            this.recognition.start();
            this.isListening = true;
            console.log('Started listening...');
        } catch (error) {
            console.error('Error starting speech recognition:', error);
            if (this.onErrorCallback) {
                this.onErrorCallback('Failed to start listening: ' + error.message);
            }
        }
    }

    stopListening() {
        if (!this.recognition || !this.isListening) return;
        
        try {
            this.recognition.stop();
            this.isListening = false;
            console.log('Stopped listening.');
        } catch (error) {
            console.error('Error stopping speech recognition:', error);
        }
    }

    restartRecognition() {
        if (this.isListening) {
            this.stopListening();
            setTimeout(() => this.startListening(), 500);
        }
    }

    setOnResult(callback) {
        this.onResultCallback = callback;
    }

    setOnError(callback) {
        this.onErrorCallback = callback;
    }

    setOnEnd(callback) {
        this.onEndCallback = callback;
    }

    async speak(text) {
        if (!text) return;

        // Cancel any ongoing speech
        this.synthesis.cancel();

        return new Promise((resolve, reject) => {
            try {
                const utterance = new SpeechSynthesisUtterance(text);
                
                utterance.onend = () => {
                    this.isSpeaking = false;
                    resolve();
                };

                utterance.onerror = (error) => {
                    this.isSpeaking = false;
                    console.error('Speech synthesis error:', error);
                    reject(error);
                };

                // Set voice preferences
                const voices = this.synthesis.getVoices();
                const preferredVoice = voices.find(voice => 
                    voice.lang.includes('en') && voice.name.includes('Female')
                ) || voices[0];
                
                if (preferredVoice) {
                    utterance.voice = preferredVoice;
                }

                utterance.rate = 1.0;
                utterance.pitch = 1.0;
                utterance.volume = 1.0;

                this.isSpeaking = true;
                this.synthesis.speak(utterance);

                // Safety timeout
                setTimeout(() => {
                    if (this.isSpeaking) {
                        this.isSpeaking = false;
                        this.synthesis.cancel();
                        resolve();
                    }
                }, 10000);
            } catch (error) {
                console.error('Error in speak:', error);
                this.isSpeaking = false;
                reject(error);
            }
        });
    }
} 