document.addEventListener('DOMContentLoaded', function() {
    // Check browser support for speech recognition
    if (!('SpeechRecognition' in window) && !('webkitSpeechRecognition' in window)) {
        document.querySelectorAll('.mic-button').forEach(button => {
            button.style.display = 'none';
        });
        console.error('Speech recognition is not supported in this browser');
        return;
    }

    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    let isRecording = false;
    let currentInput = null;
    let currentButton = null;

    recognition.onstart = function() {
        isRecording = true;
        if (currentButton) {
            currentButton.classList.add('recording');
            currentButton.innerHTML = '<i class="fas fa-microphone-slash"></i>';
            currentButton.title = 'Click to stop voice input';
        }
    };

    recognition.onend = function() {
        isRecording = false;
        if (currentButton) {
            currentButton.classList.remove('recording');
            currentButton.innerHTML = '<i class="fas fa-microphone"></i>';
            currentButton.title = 'Click to start voice input';
        }
        currentInput = null;
        currentButton = null;
    };

    recognition.onresult = function(event) {
        if (!currentInput) return;

        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript;
            } else {
                interimTranscript += transcript;
            }
        }

        if (finalTranscript) {
            const existingText = currentInput.value;
            const newText = existingText + (existingText && !existingText.endsWith(' ') ? ' ' : '') + finalTranscript;
            currentInput.value = newText;
            
            // Trigger input event to update any validation
            const inputEvent = new Event('input', { bubbles: true });
            currentInput.dispatchEvent(inputEvent);
        }
    };

    recognition.onerror = function(event) {
        console.error('Speech recognition error:', event.error);
        if (event.error === 'not-allowed') {
            alert('Please allow microphone access to use voice input.');
        }
        stopRecording();
    };

    function startRecording(input, button) {
        if (isRecording) {
            stopRecording();
        }
        
        try {
            currentInput = input;
            currentButton = button;
            recognition.start();
        } catch (e) {
            console.error('Failed to start recording:', e);
            alert('Failed to start voice input. Please try again.');
        }
    }

    function stopRecording() {
        if (isRecording) {
            try {
                recognition.stop();
            } catch (e) {
                console.error('Failed to stop recording:', e);
            }
        }
    }

    // Add click handlers to all mic buttons
    document.querySelectorAll('.mic-button').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('data-target');
            const input = document.getElementById(targetId);
            
            if (!isRecording || currentInput !== input) {
                startRecording(input, this);
            } else {
                stopRecording();
            }
        });
    });

    // Stop recording when switching tabs/windows
    document.addEventListener('visibilitychange', function() {
        if (document.hidden && isRecording) {
            stopRecording();
        }
    });

    // Stop recording when the form is submitted
    document.querySelector('form').addEventListener('submit', function() {
        if (isRecording) {
            stopRecording();
        }
    });
}); 