// speech.js
class SpeechHandler {
    constructor() {
        this.synth = window.speechSynthesis;
        this.utterance = null;
        this.isSpeaking = false;
    }

    speak(text) {
        // Cancel any ongoing speech
        if (this.isSpeaking) {
            this.synth.cancel();
        }

        // Create new utterance
        this.utterance = new SpeechSynthesisUtterance(text);
        
        // Configure voice
        const voices = this.synth.getVoices();
        const femaleVoice = voices.find(voice => voice.name.includes('Female') || voice.name.includes('Zira'));
        if (femaleVoice) {
            this.utterance.voice = femaleVoice;
        }
        
        // Configure speech settings
        this.utterance.rate = 1.0;  // Speed
        this.utterance.pitch = 1.0; // Pitch
        this.utterance.volume = 1.0; // Volume

        // Event handlers
        this.utterance.onstart = () => {
            this.isSpeaking = true;
            console.log('Started speaking:', text);
        };
        
        this.utterance.onend = () => {
            this.isSpeaking = false;
            console.log('Finished speaking:', text);
        };

        // Speak
        this.synth.speak(this.utterance);
    }

    stop() {
        if (this.isSpeaking) {
            this.synth.cancel();
            this.isSpeaking = false;
        }
    }
}

// Create global speech handler
window.speechHandler = new SpeechHandler();

// Initialize voices when they're loaded
window.speechSynthesis.onvoiceschanged = () => {
    console.log('Voices loaded:', window.speechSynthesis.getVoices());
}; 