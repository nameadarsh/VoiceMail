import time
import platform
import speech_recognition as sr
import pyttsx3
from typing import Optional, List, Tuple

from ..config import config
from ..utils.logger import logger

class SpeechManager:
    """Handles speech recognition and synthesis"""
    
    def __init__(self):
        """Initialize speech manager"""
        self.recognizer = self._init_recognizer()
        self.tts_engine = self._init_tts()
        self.microphone_index = config.MICROPHONE_INDEX
    
    def _init_recognizer(self) -> sr.Recognizer:
        """Initialize speech recognizer with optimal settings"""
        recognizer = sr.Recognizer()
        recognizer.pause_threshold = 1.5
        recognizer.energy_threshold = 1000
        recognizer.dynamic_energy_threshold = True
        recognizer.dynamic_energy_adjustment_damping = 0.15
        recognizer.dynamic_energy_ratio = 1.5
        recognizer.operation_timeout = None
        return recognizer
    
    def _init_tts(self) -> Optional[pyttsx3.Engine]:
        """Initialize text-to-speech engine"""
        try:
            engine = pyttsx3.init()
            
            # Get available voices
            voices = engine.getProperty('voices')
            logger.info(f"Available voices: {[voice.name for voice in voices]}")
            
            # Try to set a female voice if available
            for voice in voices:
                if "female" in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    logger.info(f"Using voice: {voice.name}")
                    break
            
            # Set properties for better clarity
            engine.setProperty('rate', 150)
            engine.setProperty('volume', 1.0)
            
            # Test the voice
            logger.info("Testing TTS...")
            engine.say("Testing voice output")
            engine.runAndWait()
            logger.info("TTS test complete")
            
            return engine
        except Exception as e:
            logger.error(f"Error initializing TTS: {e}")
            return None
    
    def get_available_microphones(self) -> List[Tuple[int, str]]:
        """Get list of available microphones"""
        try:
            return list(enumerate(sr.Microphone.list_microphone_names()))
        except Exception as e:
            logger.error(f"Error getting microphone list: {e}")
            return []
    
    def set_microphone(self, index: int) -> bool:
        """Set microphone by index"""
        try:
            with sr.Microphone(device_index=index) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                self.microphone_index = index
                logger.info(f"Successfully set microphone to index {index}")
                return True
        except Exception as e:
            logger.error(f"Error setting microphone: {e}")
            return False
    
    def detect_microphone(self) -> Optional[int]:
        """Automatically detect a working microphone"""
        try:
            mics = self.get_available_microphones()
            for index, name in mics:
                logger.info(f"Testing microphone {index}: {name}")
                if self.set_microphone(index):
                    return index
            return None
        except Exception as e:
            logger.error(f"Error detecting microphone: {e}")
            return None
    
    def speak(self, text: str) -> bool:
        """Convert text to speech"""
        try:
            if not self.tts_engine:
                logger.warning("TTS engine not initialized")
                return False
            
            logger.info(f"Speaking: {text}")
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            time.sleep(0.5)  # Small pause after speaking
            return True
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
            return False
    
    def listen(self, timeout: int = None) -> Optional[str]:
        """Listen for speech input"""
        try:
            if self.microphone_index is None:
                detected = self.detect_microphone()
                if detected is None:
                    logger.error("No working microphone found")
                    return None
                self.microphone_index = detected
            
            with sr.Microphone(device_index=self.microphone_index) as source:
                logger.info("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                logger.info("Listening for voice input...")
                audio = self.recognizer.listen(source, timeout=timeout)
                
                logger.info("Recognizing speech...")
                text = self.recognizer.recognize_google(audio, language='en-IN')
                logger.info(f"Recognized: {text}")
                return text.lower()
        except sr.WaitTimeoutError:
            logger.warning("Timeout waiting for voice input")
            return None
        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in speech recognition: {e}")
            return None
    
    def listen_with_retry(self, prompt: str, max_attempts: int = None, timeout: int = None) -> Optional[str]:
        """Listen for speech input with retry mechanism"""
        if max_attempts is None:
            max_attempts = config.MAX_RETRIES
        if timeout is None:
            timeout = config.SPEECH_TIMEOUT
        
        for attempt in range(max_attempts):
            logger.info(f"Attempt {attempt + 1} of {max_attempts}")
            if prompt:
                self.speak(prompt)
                time.sleep(0.5)
            
            response = self.listen(timeout=timeout)
            if response:
                return response
            
            if attempt < max_attempts - 1:
                logger.info("No response received, retrying...")
                self.speak("I didn't catch that. Please try again.")
                time.sleep(0.5)
        
        logger.warning("Max attempts reached, no valid input received")
        return None

# Create global speech manager instance
speech_manager = SpeechManager() 